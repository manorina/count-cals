const input = document.getElementById("food-search");
const results = document.getElementById("results");
const form = document.getElementById("log-form");
const foodIdInput = document.getElementById("food_id");
const foodName = document.getElementById("food-name");

let timeout = null;

input.addEventListener("input", () => {
  clearTimeout(timeout);

  const q = input.value.trim();
  if (q.length < 2) {
    results.innerHTML = "";
    return;
  }

  timeout = setTimeout(() => {
    fetch(`/foods/search?q=${encodeURIComponent(q)}`)
      .then(r => r.json())
      .then(data => {
        results.innerHTML = "";
        data.forEach(food => {
          const li = document.createElement("li");
          li.textContent = `${food.name} (${food.energy_kj_100g} kJ / 100g)`;
          li.onclick = () => selectFood(food);
          results.appendChild(li);
        });
      });
  }, 300);
});

function selectFood(food) {
  foodIdInput.value = food.id;
  foodName.textContent = food.name;
  form.style.display = "block";
  results.innerHTML = "";
  input.value = food.name;
}
