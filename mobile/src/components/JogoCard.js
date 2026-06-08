// Cartão de um jogo com formulário de palpite.
// No mata-mata, se o palpite for empate, mostra "Quem avança?" (dois botões).
import React, { useState } from "react";
import {
  ActivityIndicator,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { api } from "../api/client";
import { colors } from "../theme";

function StatusBadge({ status, label }) {
  const map = {
    aberto: [colors.successLight, colors.success],
    fechado: [colors.warningLight, colors.warning],
    finalizado: ["#e2e8f0", colors.textMuted],
  };
  const [bg, fg] = map[status] || ["#e2e8f0", colors.textMuted];
  return (
    <View style={[styles.badge, { backgroundColor: bg }]}>
      <Text style={[styles.badgeText, { color: fg }]}>{label}</Text>
    </View>
  );
}

export default function JogoCard({ jogo, onSaved }) {
  const p = jogo.palpite;
  const [casa, setCasa] = useState(
    p ? String(p.gols_casa_palpite) : ""
  );
  const [fora, setFora] = useState(
    p ? String(p.gols_fora_palpite) : ""
  );
  const [classificado, setClassificado] = useState(
    p ? p.classificado_palpite : null
  );
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState(null);
  const [ok, setOk] = useState(false);

  const travado = jogo.travado;
  const empate =
    casa !== "" && fora !== "" && parseInt(casa, 10) === parseInt(fora, 10);
  const precisaClassificado = jogo.is_mata_mata && empate;

  async function salvar() {
    setErro(null);
    setOk(false);
    const gc = parseInt(casa, 10);
    const gf = parseInt(fora, 10);
    if (Number.isNaN(gc) || Number.isNaN(gf)) {
      setErro("Informe os dois placares.");
      return;
    }
    if (precisaClassificado && !classificado) {
      setErro("Empate no mata-mata: escolha quem avança.");
      return;
    }
    setSalvando(true);
    try {
      const atualizado = await api(`/palpites/${jogo.id}`, {
        method: "POST",
        body: {
          gols_casa_palpite: gc,
          gols_fora_palpite: gf,
          classificado_palpite: empate ? classificado : null,
        },
      });
      setOk(true);
      onSaved && onSaved(atualizado);
    } catch (e) {
      setErro(e.message);
    } finally {
      setSalvando(false);
    }
  }

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <Text style={styles.data}>{jogo.data_fmt}</Text>
        {travado ? (
          <StatusBadge status="fechado" label="🔒 Travado" />
        ) : (
          <StatusBadge status="aberto" label="Aberto" />
        )}
      </View>

      <View style={styles.row}>
        <Text style={styles.time} numberOfLines={1}>
          {jogo.time_casa}
        </Text>
        <TextInput
          style={[styles.input, travado && styles.inputDisabled]}
          value={casa}
          onChangeText={setCasa}
          keyboardType="number-pad"
          maxLength={2}
          editable={!travado}
          placeholder="-"
        />
        <Text style={styles.x}>x</Text>
        <TextInput
          style={[styles.input, travado && styles.inputDisabled]}
          value={fora}
          onChangeText={setFora}
          keyboardType="number-pad"
          maxLength={2}
          editable={!travado}
          placeholder="-"
        />
        <Text style={styles.time} numberOfLines={1}>
          {jogo.time_fora}
        </Text>
      </View>

      {/* Resultado oficial, quando houver */}
      {jogo.tem_resultado && (
        <Text style={styles.resultado}>
          Resultado: {jogo.gols_casa_real} x {jogo.gols_fora_real}
          {jogo.classificado_real ? `  ·  ✓ ${jogo.classificado_real}` : ""}
          {p ? `   |   seus pontos: +${p.pontos}` : ""}
        </Text>
      )}

      {/* Quem avança? (mata-mata + empate) */}
      {precisaClassificado && !travado && (
        <View style={styles.avanca}>
          <Text style={styles.avancaLabel}>Empate — quem avança?</Text>
          <View style={styles.avancaRow}>
            {[jogo.time_casa, jogo.time_fora].map((t) => (
              <TouchableOpacity
                key={t}
                style={[
                  styles.avancaBtn,
                  classificado === t && styles.avancaBtnAtivo,
                ]}
                onPress={() => setClassificado(t)}
              >
                <Text
                  style={[
                    styles.avancaBtnText,
                    classificado === t && styles.avancaBtnTextAtivo,
                  ]}
                >
                  {t}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      )}

      {erro && <Text style={styles.erro}>{erro}</Text>}
      {ok && <Text style={styles.ok}>✓ Palpite salvo!</Text>}

      {!travado ? (
        <TouchableOpacity
          style={styles.salvar}
          onPress={salvar}
          disabled={salvando}
        >
          {salvando ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.salvarText}>
              {p ? "Atualizar palpite" : "Salvar palpite"}
            </Text>
          )}
        </TouchableOpacity>
      ) : p ? (
        <Text style={styles.travadoInfo}>
          Seu palpite: {p.gols_casa_palpite} x {p.gols_fora_palpite}
          {jogo.is_mata_mata && p.classificado_palpite
            ? ` · avança: ${p.classificado_palpite}`
            : ""}
        </Text>
      ) : (
        <Text style={styles.travadoInfo}>Sem palpite registrado.</Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.card,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 14,
    marginBottom: 12,
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 10,
  },
  data: { fontSize: 12, color: colors.textFaint, fontWeight: "500" },
  badge: { borderRadius: 999, paddingHorizontal: 10, paddingVertical: 3 },
  badgeText: { fontSize: 11, fontWeight: "700" },
  row: { flexDirection: "row", alignItems: "center", justifyContent: "center" },
  time: {
    flex: 1,
    fontSize: 13,
    fontWeight: "600",
    color: colors.text,
    textAlign: "center",
  },
  input: {
    width: 46,
    height: 46,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 10,
    textAlign: "center",
    fontSize: 18,
    fontWeight: "700",
    color: colors.text,
    marginHorizontal: 4,
  },
  inputDisabled: { backgroundColor: "#f1f5f9", color: colors.textFaint },
  x: { color: colors.textFaint, marginHorizontal: 2 },
  resultado: {
    marginTop: 10,
    fontSize: 12,
    color: colors.textMuted,
    textAlign: "center",
  },
  avanca: { marginTop: 12 },
  avancaLabel: {
    fontSize: 12,
    color: colors.textMuted,
    marginBottom: 6,
    fontWeight: "500",
  },
  avancaRow: { flexDirection: "row", gap: 8 },
  avancaBtn: {
    flex: 1,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 10,
    paddingVertical: 10,
    alignItems: "center",
  },
  avancaBtnAtivo: { backgroundColor: colors.brand, borderColor: colors.brand },
  avancaBtnText: { fontSize: 13, fontWeight: "600", color: colors.text },
  avancaBtnTextAtivo: { color: "#fff" },
  erro: { color: colors.danger, fontSize: 12, marginTop: 8, textAlign: "center" },
  ok: { color: colors.success, fontSize: 12, marginTop: 8, textAlign: "center" },
  salvar: {
    marginTop: 12,
    backgroundColor: colors.brand,
    borderRadius: 10,
    paddingVertical: 11,
    alignItems: "center",
  },
  salvarText: { color: "#fff", fontWeight: "700", fontSize: 14 },
  travadoInfo: {
    marginTop: 10,
    fontSize: 12,
    color: colors.textMuted,
    textAlign: "center",
  },
});
