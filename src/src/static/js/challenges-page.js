// Challenges Page JavaScript

const levelsDropdown = document.getElementById("levelsDropdown");
const statusDropdown = document.getElementById('statusDropdown');

function filterChallenges() {
  const selectedLevel = levelsDropdown.value.toLowerCase();
  const selectedStatus = statusDropdown ? statusDropdown.value : 'all';
  const challengeCards = document.querySelectorAll('.challenge-card');

  challengeCards.forEach((card) => {
    const cardLevel = card.getAttribute('data-level');
    const cardStatus = card.getAttribute('data-status');
    const matchesLevel = selectedLevel === 'all' || cardLevel === selectedLevel;
    let matchesStatus = false;
    if (selectedStatus === 'all') matchesStatus = true;
    else matchesStatus = cardStatus && cardStatus.split(' ').includes(selectedStatus);
    card.style.display = (matchesLevel && matchesStatus) ? 'flex' : 'none';
  });
}

if (levelsDropdown) {
  levelsDropdown.addEventListener('change', filterChallenges);
}
if (statusDropdown) {
  statusDropdown.addEventListener('change', filterChallenges);
}

// Initial filter on page load
filterChallenges();
