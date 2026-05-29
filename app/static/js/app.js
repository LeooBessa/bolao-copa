// JavaScript do front-end do bolão.
// Responsabilidades:
//  1. Menu mobile (toggle).
//  2. Mata-mata: mostrar/esconder o seletor "quem avança?" quando o palpite
//     for empate.

(function () {
  "use strict";

  // --- Menu mobile ------------------------------------------------------
  const menuBtn = document.getElementById("menu-btn");
  const mobileMenu = document.getElementById("mobile-menu");
  if (menuBtn && mobileMenu) {
    menuBtn.addEventListener("click", function () {
      mobileMenu.classList.toggle("hidden");
    });
  }

  // --- Mata-mata: "quem avança?" ---------------------------------------
  function atualizarQuemAvanca(form) {
    if (form.dataset.mataMata !== "1") return;
    const inputs = form.querySelectorAll(".placar-input");
    if (inputs.length < 2) return;

    const casa = parseInt(inputs[0].value, 10);
    const fora = parseInt(inputs[1].value, 10);
    const bloco = form.querySelector(".quem-avanca");
    const select = bloco ? bloco.querySelector("select") : null;
    if (!bloco) return;

    // Empate (ambos preenchidos e iguais) => mostra o seletor.
    const empate =
      !Number.isNaN(casa) && !Number.isNaN(fora) && casa === fora;

    if (empate) {
      bloco.classList.remove("hidden");
      if (select) select.required = true;
    } else {
      bloco.classList.add("hidden");
      if (select) {
        select.required = false;
        select.value = ""; // limpa: não faz sentido fora do empate
      }
    }
  }

  document.querySelectorAll(".palpite-form").forEach(function (form) {
    // Estado inicial.
    atualizarQuemAvanca(form);
    // Reage a mudanças nos placares.
    form.querySelectorAll(".placar-input").forEach(function (input) {
      input.addEventListener("input", function () {
        atualizarQuemAvanca(form);
      });
    });
  });
})();
