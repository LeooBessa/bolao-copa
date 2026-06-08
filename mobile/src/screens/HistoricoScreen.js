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
import { useAuth } from "../context/AuthContext";
import { colors } from "../theme";

export default function HistoricoScreen() {
  const { usuario, sair } = useAuth();
  const [itens, setItens] = useState([]);
  const [carregando, setCarregando] = useState(true);
  const [atualizando, setAtualizando] = useState(false);

  const carregar = useCallback(async () => {
    try {
      setItens(await api("/historico"));
    } catch (_) {
    } finally {
      setCarregando(false);
      setAtualizando(false);
    }
  }, []);

  useEffect(() => {
    carregar();
  }, [carregar]);

  if (carregando) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={colors.brand} />
      </View>
    );
  }

  function corPontos(p) {
    if (!p) return colors.textFaint;
    if (p.pontos === 3) return colors.success;
    if (p.pontos === 1) return colors.brand;
    return colors.textFaint;
  }

  return (
    <FlatList
      style={styles.container}
      contentContainerStyle={styles.lista}
      data={itens}
      keyExtractor={(item) => String(item.id)}
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
      ListHeaderComponent={
        <View style={styles.header}>
          <View>
            <Text style={styles.titulo}>Histórico</Text>
            <Text style={styles.sub}>
              Olá, {usuario?.nome} · {usuario?.pontos ?? 0} pts
              {usuario?.posicao ? ` · ${usuario.posicao}º lugar` : ""}
            </Text>
          </View>
          <Text style={styles.sair} onPress={sair}>
            Sair
          </Text>
        </View>
      }
      renderItem={({ item }) => {
        const p = item.palpite;
        return (
          <View style={styles.card}>
            <View style={{ flex: 1 }}>
              <Text style={styles.jogo}>
                {item.time_casa} x {item.time_fora}
              </Text>
              <Text style={styles.fase}>{item.fase_label}</Text>
            </View>
            <View style={styles.meio}>
              <Text style={styles.resultado}>
                {item.gols_casa_real} x {item.gols_fora_real}
              </Text>
              <Text style={styles.palpite}>
                {p ? `palpite ${p.gols_casa_palpite}x${p.gols_fora_palpite}` : "sem palpite"}
              </Text>
            </View>
            <Text style={[styles.pontos, { color: corPontos(p) }]}>
              +{p ? p.pontos : 0}
            </Text>
          </View>
        );
      }}
      ListEmptyComponent={
        <Text style={styles.vazio}>Nenhum jogo finalizado ainda.</Text>
      }
    />
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  center: { flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: colors.bg },
  lista: { padding: 16 },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 14,
  },
  titulo: { fontSize: 22, fontWeight: "800", color: colors.text },
  sub: { fontSize: 13, color: colors.textMuted, marginTop: 2 },
  sair: { color: colors.danger, fontWeight: "700", fontSize: 14, padding: 4 },
  card: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: colors.card,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 12,
    marginBottom: 8,
  },
  jogo: { fontSize: 14, fontWeight: "600", color: colors.text },
  fase: { fontSize: 11, color: colors.textFaint, marginTop: 2 },
  meio: { alignItems: "center", marginHorizontal: 10 },
  resultado: { fontSize: 14, fontWeight: "700", color: colors.text },
  palpite: { fontSize: 11, color: colors.textFaint, marginTop: 2 },
  pontos: { fontSize: 18, fontWeight: "800", width: 42, textAlign: "right" },
  vazio: { textAlign: "center", color: colors.textFaint, marginTop: 40 },
});
