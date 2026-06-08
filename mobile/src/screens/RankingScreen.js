import React, { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { api } from "../api/client";
import { useShake } from "../hooks/useShake";
import { colors } from "../theme";

function medalha(pos) {
  return pos === 1 ? "🥇" : pos === 2 ? "🥈" : pos === 3 ? "🥉" : `${pos}`;
}

export default function RankingScreen() {
  const [linhas, setLinhas] = useState([]);
  const [carregando, setCarregando] = useState(true);
  const [atualizando, setAtualizando] = useState(false);

  const carregar = useCallback(async () => {
    try {
      setLinhas(await api("/ranking"));
    } catch (_) {
    } finally {
      setCarregando(false);
      setAtualizando(false);
    }
  }, []);

  useEffect(() => {
    carregar();
  }, [carregar]);

  useShake(() => {
    setAtualizando(true);
    carregar();
  });

  if (carregando) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={colors.brand} />
      </View>
    );
  }

  return (
    <FlatList
      style={styles.container}
      contentContainerStyle={styles.lista}
      data={linhas}
      keyExtractor={(item) => String(item.usuario_id)}
      ListHeaderComponent={
        <Text style={styles.titulo}>Ranking geral</Text>
      }
      refreshControl={
        <RefreshControl
          refreshing={atualizando}
          onRefresh={() => {
            setAtualizando(true);
            carregar();
          }}
          colors={[colors.brand]}
        />
      }
      renderItem={({ item }) => (
        <View style={[styles.linha, item.eu && styles.linhaEu]}>
          <Text style={styles.pos}>{medalha(item.posicao)}</Text>
          <View style={{ flex: 1 }}>
            <Text style={styles.nome}>
              {item.nome}
              {item.eu ? "  (você)" : ""}
            </Text>
            <Text style={styles.detalhe}>
              {item.acertos} acertos · {item.total_palpites} palpites
            </Text>
          </View>
          <Text style={styles.pontos}>{item.pontos}</Text>
        </View>
      )}
      ListEmptyComponent={
        <Text style={styles.vazio}>Nenhum participante ainda.</Text>
      }
    />
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  center: { flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: colors.bg },
  lista: { padding: 16 },
  titulo: { fontSize: 22, fontWeight: "800", color: colors.text, marginBottom: 12 },
  linha: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: colors.card,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 12,
    marginBottom: 8,
  },
  linhaEu: { backgroundColor: colors.brandLight, borderColor: colors.brand },
  pos: { width: 36, fontSize: 16, fontWeight: "700", color: colors.textMuted },
  nome: { fontSize: 15, fontWeight: "600", color: colors.text },
  detalhe: { fontSize: 12, color: colors.textFaint, marginTop: 2 },
  pontos: { fontSize: 20, fontWeight: "800", color: colors.brand },
  vazio: { textAlign: "center", color: colors.textFaint, marginTop: 40 },
});
