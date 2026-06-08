// Hook que usa o SENSOR acelerômetro do dispositivo (expo-sensors).
// Detecta quando o usuário "chacoalha" o celular e dispara um callback —
// usado como "chacoalhar para atualizar" os dados.
//
// Esta é a integração de coleta de dados via sensor exigida no projeto.
import { useEffect, useRef } from "react";
import { Accelerometer } from "expo-sensors";

const LIMITE_SHAKE = 1.8; // força (g) acima da gravidade para contar como shake
const INTERVALO_MS = 1200; // evita disparos repetidos

export function useShake(onShake) {
  const ultimoDisparo = useRef(0);

  useEffect(() => {
    Accelerometer.setUpdateInterval(200);
    const sub = Accelerometer.addListener(({ x, y, z }) => {
      // Magnitude do vetor de aceleração (em repouso ≈ 1g).
      const forca = Math.sqrt(x * x + y * y + z * z);
      const agora = Date.now();
      if (forca > LIMITE_SHAKE && agora - ultimoDisparo.current > INTERVALO_MS) {
        ultimoDisparo.current = agora;
        onShake && onShake();
      }
    });
    return () => sub && sub.remove();
  }, [onShake]);
}
