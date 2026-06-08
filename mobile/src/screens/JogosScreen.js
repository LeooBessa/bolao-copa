// Tela de jogos + palpites. Usa o SENSOR (acelerômetro) para "chacoalhar
// para atualizar" e também pull-to-refresh.
import React, { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  RefreshControl,
  SectionList,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { api } from "../api/client";
import JogoCard from "../components/JogoCard";
import { useShake } from "../hooks/useShake";
import { colors } from "../theme";

export default function JogosScreen() {
  const [jogos, setJogos] = useState([]);
  const [carregando, setCarregando] = useState(true);
  const [atualizando, setAtualizando] = useState(false);
  const [erro, setErro] = useState(null);
  const [aviso, setAviso] = useState(null);

  const carregar = useCallback(async (silencioso = false) => {
    if (!silencioso) setErro(null);
    try {
      const data = await api("/jogos");
      setJogos(data);
    } catch (e) {
      setErro(e.message);
    } finally {
      setCarregando(false);
      setAtualizando(false);
    }
  }, []);

  useEffect(() => {
    carregar();
  }, [carregar]);

  // SENSOR: chacoalhar o celular recarrega os jogos.
  useShake(() => {
    setAviso("🔄 Atualizado (chacoalhada detectada)");
    setAtualizando(true);
    carregar(true);
    setTimeout(() => setAviso(null), 1800);
  });

  function onSaved(jogoAtualizado) {
    setJogos((prev) =>
      prev.map((j) => (j.id === jogoAtualizado.id ? jogoAtualizado : j))
    );
  }

  // Agrupa por fase para a SectionList.
  const secoes = [];
  let faseAtual = null;
  for (const j of jogos) {
    if (j.fase !== faseAtual) {
      faseAtual = j.fase;
      secoes.push({ title: j.fase_label, data: [] });
    }
    secoes[secoes.length - 1].data.push(j);
  }

  if (carregando) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={colors.brand} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.dica}>💡 Dica: chacoalhe o celular para atualizar.</Text>
      {aviso && <Text style={styles.aviso}>{aviso}</Text>}
      {erro && <Text style={styles.erro}>{erro}</Text>}
      <SectionList
        sections={secoes}
        keyExtractor={(item) => String(item.id)}
        renderItem={({ item }) => <JogoCard jogo={item} onSaved={onSaved} />}
        renderSectionHeader={({ section }) => (
          <Text style={styles.secaoTitulo}>{section.title}</Text>
        )}
        contentContainerStyle={styles.lista}
        stickySectionHeadersEnabled={false}
        refreshControl={
          <RefreshControl
            refreshing={atualizando}
            onRefresh={() => {
              setAtualizando(true);
              carregar();
            }}
            colors={[colors.brand]}
            tintColor={colors.brand}
          />
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  center: { flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: colors.bg },
  lista: { padding: 16, paddingBottom: 32 },
  dica: {
    textAlign: "center",
    fontSize: 12,
    color: colors.textMuted,
    paddingTop: 10,
  },
  aviso: {
    textAlign: "center",
    fontSize: 13,
    color: colors.success,
    backgroundColor: colors.successLight,
    marginHorizontal: 16,
    marginTop: 8,
    paddingVertical: 6,
    borderRadius: 8,
    overflow: "hidden",
  },
  erro: { textAlign: "center", color: colors.danger, marginTop: 8 },
  secaoTitulo: {
    fontSize: 12,
    fontWeight: "800",
    color: colors.textFaint,
    textTransform: "uppercase",
    letterSpacing: 0.5,
    marginTop: 14,
    marginBottom: 8,
  },
});
