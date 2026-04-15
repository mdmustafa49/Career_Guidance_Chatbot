// ── Configuration ───────────────────────────────────────────────────────────
const API_URL = "http://127.0.0.1:5000/api/chat";
const STORAGE_KEY = "career_chat_history";
const MAX_HISTORY = 50;

// ── State ───────────────────────────────────────────────────────────────────
let msgCount = 0;
let topicsSet = new Set();
let confidenceSum = 0;
let isTyping = false;
let chatHistory = [];

// ── DOM Elements ───────────────────────────────────────────────────────────
const elements = {
  messages: document.getElementById("messages"),
  input: document.getElementById("user-input"),
  sendBtn: document.getElementById("send-btn"),
  typing: document.getElementById("typing"),
  msgCount: document.getElementById("msg-count"),
  topicCount: document.getElementById("topic-count"),
  confAvg: document.getElementById("confidence-avg"),
  charCount: document.getElementById("char-count"),
  statusText: document.getElementById("status-text"),
  welcome: document.getElementById("welcome-screen"),
  sidebar: document.getElementById("sidebar")
};

// ── Initialization ─────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  loadTheme();
  loadChatHistory();
  setupEventListeners();
  elements.input.focus();
});

function setupEventListeners() {
  // Auto-resize textarea
  elements.input.addEventListener("input", function() {
    this.style.height = "auto";
    this.style.height = Math.min(this.scrollHeight, 120) + "px";
    updateCharCount();
  });
  
  // Send on Enter (but Shift+Enter for new line)
  elements.input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
  
  // Close sidebar when clicking outside on mobile
  document.addEventListener("click", (e) => {
    if (window.innerWidth <= 968 && 
        elements.sidebar.classList.contains("open") &&
        !elements.sidebar.contains(e.target) &&
        !e.target.closest(".sidebar-toggle")) {
      toggleSidebar();
    }
  });
}

// ── Theme Management ───────────────────────────────────────────────────────
function toggleTheme() {
  const isDark = document.body.classList.toggle("dark-theme");
  localStorage.setItem("theme", isDark ? "dark" : "light");
  updateThemeIcon(isDark);
}

function loadTheme() {
  const saved = localStorage.getItem("theme");
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const isDark = saved === "dark" || (!saved && prefersDark);
  
  if (isDark) document.body.classList.add("dark-theme");
  updateThemeIcon(isDark);
}

function updateThemeIcon(isDark) {
  const icon = document.getElementById("theme-icon");
  icon.className = isDark ? "fas fa-sun" : "fas fa-moon";
}

// ── Sidebar Toggle ───────────────────────────────────────────────────────────
function toggleSidebar() {
  elements.sidebar.classList.toggle("open");
}

// ── Chat History Management ────────────────────────────────────────────────
function loadChatHistory() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      chatHistory = JSON.parse(saved);
      if (chatHistory.length > 0) {
        hideWelcome();
        chatHistory.forEach(msg => {
          if (msg.type === "user") {
            appendUserMessage(msg.text, msg.timestamp, false);
          } else {
            appendBotMessage(msg.text, msg.intent, msg.confidence, msg.timestamp, false);
          }
        });
        scrollToBottom();
      }
    }
  } catch (e) {
    console.error("Failed to load history", e);
  }
}

function saveHistory() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(chatHistory.slice(-MAX_HISTORY)));
  } catch (e) {
    console.error("Failed to save history", e);
  }
}

function addToHistory(item) {
  chatHistory.push({ ...item, timestamp: new Date().toISOString() });
  saveHistory();
}

// ── Message Sending ─────────────────────────────────────────────────────────
function sendQuick(text) {
  elements.input.value = text;
  elements.input.style.height = "auto";
  updateCharCount();
  sendMessage();
  if (window.innerWidth <= 968) toggleSidebar();
}

async function sendMessage() {
  const text = elements.input.value.trim();
  if (!text || isTyping) return;

  // Clear input
  elements.input.value = "";
  elements.input.style.height = "auto";
  updateCharCount();
  hideWelcome();
  
  // Add user message
  const userMsg = { type: "user", text };
  addToHistory(userMsg);
  appendUserMessage(text, null, true);
  
  // Show typing
  setTyping(true);
  updateStatus("Career Advisor is typing...");
  
  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text })
    });
    
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    
    const data = await response.json();
    
    // Simulate natural typing delay based on response length
    const delay = Math.min(1000 + (data.response.length * 10), 2000);
    await sleep(delay);
    
    // Add bot message
    setTyping(false);
    updateStatus("Online");
    
    const botMsg = { 
      type: "bot", 
      text: data.response, 
      intent: data.intent, 
      confidence: data.confidence 
    };
    addToHistory(botMsg);
    appendBotMessage(data.response, data.intent, data.confidence, null, true);
    updateStats(data.intent, data.confidence);
    
  } catch (error) {
    setTyping(false);
    updateStatus("Error - Retrying...");
    
    const errorMsg = error.message.includes("fetch") || error.message.includes("Network") 
      ? "⚠️ Connection lost. Please check that the Flask server is running (python backend/app.py) and refresh."
      : "⚠️ Something went wrong. Please try again.";
    
    appendBotMessage(errorMsg, "error", 0, null, true);
    console.error("Chat error:", error);
  }
}

// ── Message Rendering ─────────────────────────────────────────────────────────
function appendUserMessage(text, timestamp, animate) {
  const time = timestamp ? formatTime(timestamp) : getCurrentTime();
  const div = document.createElement("div");
  div.className = `message user ${animate ? 'animate' : ''}`;
  div.innerHTML = `
    <div class="message-bubble">
      ${escapeHtml(text)}
      <div class="message-meta">
        <span>${time}</span>
      </div>
    </div>
  `;
  elements.messages.appendChild(div);
  scrollToBottom();
}

function appendBotMessage(text, intent, confidence, timestamp, animate) {
  const time = timestamp ? formatTime(timestamp) : getCurrentTime();
  const div = document.createElement("div");
  div.className = `message bot ${animate ? 'animate' : ''}`;
  
  let intentBadge = "";
  if (intent && intent !== "error" && intent !== "unknown") {
    intentBadge = `<span class="intent-badge">${intent.replace(/_/g, " ")}</span>`;
  }
  
  div.innerHTML = `
    <div class="message-bubble">
      ${formatBotText(text)}
      ${intentBadge}
      <div class="message-meta">
        <span>${time}</span>
        <button class="copy-btn" onclick="copyMessage(this)" title="Copy response">
          <i class="fas fa-copy"></i> Copy
        </button>
      </div>
    </div>
  `;
  elements.messages.appendChild(div);
  scrollToBottom();
}

function formatBotText(text) {
  // Convert **bold** to <strong>
  let html = escapeHtml(text);
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  // Convert newlines to <br>
  html = html.replace(/\n/g, "<br>");
  // Convert URLs to links
  html = html.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" class="chat-link">$1</a>');
  return html;
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

// ── UI Helpers ─────────────────────────────────────────────────────────────
function hideWelcome() {
  if (elements.welcome) {
    elements.welcome.style.display = "none";
  }
}

function setTyping(show) {
  isTyping = show;
  elements.typing.style.display = show ? "block" : "none";
  elements.sendBtn.disabled = show;
  if (show) scrollToBottom();
}

function updateStatus(text) {
  elements.statusText.textContent = text;
}

function updateCharCount() {
  const len = elements.input.value.length;
  elements.charCount.textContent = `${len}/500`;
  elements.charCount.style.color = len > 450 ? "#ef4444" : "var(--text-light)";
}

function scrollToBottom() {
  setTimeout(() => {
    elements.messages.scrollTop = elements.messages.scrollHeight;
  }, 50);
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function getCurrentTime() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function formatTime(isoString) {
  return new Date(isoString).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

// ── Statistics ─────────────────────────────────────────────────────────────
function updateStats(intent, confidence) {
  msgCount++;
  elements.msgCount.textContent = msgCount;
  
  if (intent && intent !== "error" && intent !== "unknown") {
    topicsSet.add(intent);
    elements.topicCount.textContent = topicsSet.size;
  }
  
  if (confidence > 0) {
    confidenceSum += confidence;
    const avg = Math.round((confidenceSum / msgCount) * 100);
    elements.confAvg.textContent = avg + "%";
  }
}

// ── Actions ──────────────────────────────────────────────────────────────────
function clearChat() {
  if (confirm("Start a new chat? This will clear the current conversation.")) {
    elements.messages.innerHTML = "";
    elements.messages.appendChild(elements.welcome);
    elements.welcome.style.display = "flex";
    chatHistory = [];
    localStorage.removeItem(STORAGE_KEY);
    msgCount = 0;
    topicsSet.clear();
    confidenceSum = 0;
    elements.msgCount.textContent = "0";
    elements.topicCount.textContent = "0";
    elements.confAvg.textContent = "0%";
  }
}

function copyMessage(btn) {
  const bubble = btn.closest(".message-bubble");
  const text = bubble.childNodes[0].textContent.trim();
  navigator.clipboard.writeText(text).then(() => {
    const original = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-check"></i> Copied';
    setTimeout(() => btn.innerHTML = original, 2000);
  });
}

function exportChat() {
  if (chatHistory.length === 0) {
    alert("No messages to export yet!");
    return;
  }
  
  let content = "# Career Guidance Chat - Export\n\n";
  chatHistory.forEach(msg => {
    const time = new Date(msg.timestamp).toLocaleString();
    const sender = msg.type === "user" ? "You" : "Career Advisor";
    content += `[${time}] ${sender}:\n${msg.text}\n\n`;
  });
  
  const blob = new Blob([content], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `career-chat-${new Date().toISOString().split("T")[0]}.txt`;
  a.click();
  URL.revokeObjectURL(url);
}
