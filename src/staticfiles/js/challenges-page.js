// Challenges Page JavaScript

const levelsDropdown = document.getElementById("levelsDropdown");

function filterChallenges() {
  const selectedLevel = levelsDropdown.value.toLowerCase();
  const challengeCards = document.querySelectorAll(".challenge-card");

  challengeCards.forEach((card) => {
    const cardLevel = card.getAttribute("data-level");
    const matchesLevel = selectedLevel === "all" || cardLevel === selectedLevel;

    if (matchesLevel) {
      card.style.display = "flex";
    } else {
      card.style.display = "none";
    }
  });
}

if (levelsDropdown) {
  levelsDropdown.addEventListener("change", filterChallenges);
}
