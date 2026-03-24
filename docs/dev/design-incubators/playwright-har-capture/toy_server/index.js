async function loadConversation() {
  const res = await fetch("api/conversation");
  const data = await res.json();
  document.getElementById("output").textContent = JSON.stringify(data, null, 2);
}

document.getElementById("refresh").addEventListener("click", loadConversation);
loadConversation();
