(() => {
  "use strict";

  const shell = document.querySelector(".wayne-shell");
  if (!shell) return;

  const welcome = document.getElementById("wayne-welcome");
  const conversation = document.getElementById("wayne-conversation");
  const messages = document.getElementById("wayne-messages");
  const typing = document.getElementById("wayne-typing");
  const startForm = document.getElementById("wayne-start-form");
  const chatForm = document.getElementById("wayne-chat-form");
  const startInput = document.getElementById("wayne-start-input");
  const chatInput = document.getElementById("wayne-chat-input");
  const csrfToken = document.getElementById("wayne-csrf-token").value;
  let processing = false;

  function resizeInput(input) {
    input.style.height = "auto";
    input.style.height = `${Math.min(input.scrollHeight, 144)}px`;
  }

  function showConversation() {
    welcome.hidden = true;
    conversation.hidden = false;
  }

  function setBusy(busy) {
    processing = busy;
    typing.hidden = !busy;
    document.querySelectorAll(".wayne-composer button[type='submit']").forEach((button) => {
      button.disabled = busy;
    });
    if (busy) messages.scrollTop = messages.scrollHeight;
  }

  function addMessage(kind, text, data = null, isError = false) {
    const article = document.createElement("article");
    article.className = `wayne-message wayne-message-${kind}${isError ? " wayne-message-error" : ""}`;

    const content = document.createElement("div");
    content.className = "wayne-message-content";
    const paragraph = document.createElement("p");
    paragraph.className = "mb-0";
    paragraph.textContent = text;
    content.appendChild(paragraph);

    if (data && Array.isArray(data.rows) && data.rows.length && Array.isArray(data.columns)) {
      content.appendChild(buildResult(data.columns, data.rows));
    }

    article.appendChild(content);
    messages.insertBefore(article, typing);
    article.scrollIntoView({ behavior: "smooth", block: "end" });
  }

  function buildResult(columns, rows) {
    const fragment = document.createDocumentFragment();
    const meta = document.createElement("div");
    meta.className = "wayne-result-meta";

    const count = document.createElement("span");
    count.textContent = `${rows.length} result${rows.length === 1 ? "" : "s"}`;

    const copy = document.createElement("button");
    copy.type = "button";
    copy.className = "btn btn-sm btn-ghost-secondary";
    copy.innerHTML = '<i class="ti ti-copy" aria-hidden="true"></i><span> Copy CSV</span>';
    copy.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(toCsv(columns, rows));
        copy.querySelector("span").textContent = " Copied";
        setTimeout(() => { copy.querySelector("span").textContent = " Copy CSV"; }, 1600);
      } catch (_error) {
        copy.querySelector("span").textContent = " Copy failed";
      }
    });

    meta.append(count, copy);

    const wrap = document.createElement("div");
    wrap.className = "wayne-table-wrap";
    const table = document.createElement("table");
    table.className = "table table-vcenter wayne-table";

    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");
    columns.forEach((column) => {
      const th = document.createElement("th");
      th.scope = "col";
      th.textContent = column;
      headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);

    const tbody = document.createElement("tbody");
    rows.forEach((row) => {
      const tr = document.createElement("tr");
      row.forEach((value) => {
        const td = document.createElement("td");
        td.textContent = value == null ? "—" : String(value);
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });

    table.append(thead, tbody);
    wrap.appendChild(table);
    fragment.append(meta, wrap);
    return fragment;
  }

  function toCsv(columns, rows) {
    const escape = (value) => {
      const text = value == null ? "" : String(value);
      return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
    };
    return [columns, ...rows].map((row) => row.map(escape).join(",")).join("\n");
  }

  async function ask(question) {
    if (processing || !question.trim()) return;
    showConversation();
    addMessage("user", question.trim());
    startInput.value = "";
    chatInput.value = "";
    resizeInput(startInput);
    resizeInput(chatInput);
    setBusy(true);

    const body = new FormData();
    body.append("question", question.trim());
    body.append("csrf_token", csrfToken);

    try {
      const response = await fetch(shell.dataset.askUrl, { method: "POST", body });
      const data = await response.json().catch(() => ({}));
      setBusy(false);
      if (!response.ok || !data.success) {
        addMessage("wayne", data.error || "Wayne could not retrieve that minipass data. Please try again.", null, true);
      } else {
        addMessage("wayne", data.answer, data);
      }
    } catch (_error) {
      setBusy(false);
      addMessage("wayne", "Wayne could not connect. Check your connection and try again.", null, true);
    } finally {
      chatInput.focus();
    }
  }

  [startForm, chatForm].forEach((form) => {
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      ask(new FormData(form).get("question") || "");
    });
  });

  [startInput, chatInput].forEach((input) => {
    input.addEventListener("input", () => resizeInput(input));
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        ask(input.value);
      }
    });
    resizeInput(input);
  });

  startInput.focus();
})();
