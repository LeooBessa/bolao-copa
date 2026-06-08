// Contexto de autenticação: guarda token + usuário e expõe login/cadastro/logout.
import React, { createContext, useContext, useEffect, useState } from "react";
import { api, getToken, setToken } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(null);
  const [carregando, setCarregando] = useState(true);

  // Ao abrir o app, tenta restaurar a sessão a partir do token salvo.
  useEffect(() => {
    (async () => {
      const token = await getToken();
      if (token) {
        try {
          const me = await api("/me");
          setUsuario(me);
        } catch (_) {
          await setToken(null); // token inválido/expirado
        }
      }
      setCarregando(false);
    })();
  }, []);

  async function entrar(email, senha) {
    const data = await api("/auth/login", {
      method: "POST",
      auth: false,
      body: { email, senha },
    });
    await setToken(data.token);
    setUsuario(data.usuario);
  }

  async function cadastrar(nome, email, senha) {
    const data = await api("/auth/register", {
      method: "POST",
      auth: false,
      body: { nome, email, senha },
    });
    await setToken(data.token);
    setUsuario(data.usuario);
  }

  async function sair() {
    await setToken(null);
    setUsuario(null);
  }

  async function atualizarUsuario() {
    try {
      const me = await api("/me");
      setUsuario(me);
    } catch (_) {}
  }

  return (
    <AuthContext.Provider
      value={{ usuario, carregando, entrar, cadastrar, sair, atualizarUsuario }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
