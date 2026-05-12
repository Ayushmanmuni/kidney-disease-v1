(function () {
  function buildWidget() {
    if (document.getElementById("feedback-overlay")) return;

    const overlay = document.createElement("div");
    overlay.id = "feedback-overlay";
    overlay.className = "feedback-overlay";
    overlay.setAttribute("aria-hidden", "true");

    const modal = document.createElement("div");
    modal.className = "feedback-modal";
    modal.setAttribute("role", "dialog");
    modal.setAttribute("aria-modal", "true");
    modal.setAttribute("aria-labelledby", "feedback-title");

    modal.innerHTML = `
      <button type="button" class="feedback-close" id="feedback-close" aria-label="Close feedback form">&times;</button>
      <h3 id="feedback-title">Report a Bug / Feedback</h3>
      <p class="feedback-subtitle">Found a bug or UX issue? Tell us and we will improve it.</p>
      <form id="feedback-form" class="feedback-form">
        <div class="feedback-row">
          <label for="feedback-category">Type</label>
          <select id="feedback-category" name="category" required>
            <option value="bug">Bug</option>
            <option value="ui">UI/UX issue</option>
            <option value="feature">Feature request</option>
            <option value="other">Other</option>
          </select>
        </div>
        <div class="feedback-row">
          <label for="feedback-name">Name (optional)</label>
          <input id="feedback-name" name="name" type="text" maxlength="100" placeholder="Your name" />
        </div>
        <div class="feedback-row">
          <label for="feedback-email">Email (optional)</label>
          <input id="feedback-email" name="email" type="email" maxlength="120" placeholder="you@example.com" />
        </div>
        <div class="feedback-row">
          <label for="feedback-message">Describe issue</label>
          <textarea id="feedback-message" name="message" rows="5" minlength="10" maxlength="4000" required placeholder="What happened? Steps to reproduce, expected behavior, and what device/browser you used."></textarea>
        </div>
        <div class="feedback-actions">
          <button type="button" id="feedback-cancel" class="btn btn-secondary">Cancel</button>
          <button type="submit" id="feedback-submit" class="btn btn-primary">Submit</button>
        </div>
        <p id="feedback-status" class="feedback-status" aria-live="polite"></p>
      </form>
    `;

    overlay.appendChild(modal);
    document.body.appendChild(overlay);

    const open = () => {
      overlay.classList.add("show");
      overlay.setAttribute("aria-hidden", "false");
      document.body.classList.add("menu-open");
      const message = document.getElementById("feedback-message");
      if (message) setTimeout(() => message.focus(), 40);
    };

    const close = () => {
      overlay.classList.remove("show");
      overlay.setAttribute("aria-hidden", "true");
      document.body.classList.remove("menu-open");
    };

    // Allow other UI elements (like profile dropdown) to open the feedback modal.
    window.openFeedbackWidget = open;
    window.closeFeedbackWidget = close;

    const closeBtn = document.getElementById("feedback-close");
    const cancelBtn = document.getElementById("feedback-cancel");
    closeBtn.addEventListener("click", close);
    cancelBtn.addEventListener("click", close);

    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) close();
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && overlay.classList.contains("show")) {
        close();
      }
    });

    const form = document.getElementById("feedback-form");
    const status = document.getElementById("feedback-status");
    const submitBtn = document.getElementById("feedback-submit");

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      status.textContent = "";

      const payload = {
        category: document.getElementById("feedback-category").value,
        name: document.getElementById("feedback-name").value.trim(),
        email: document.getElementById("feedback-email").value.trim(),
        message: document.getElementById("feedback-message").value.trim(),
        page_url: window.location.href,
      };

      if (payload.message.length < 10) {
        status.textContent = "Please add a little more detail (minimum 10 characters).";
        status.className = "feedback-status error";
        return;
      }

      submitBtn.disabled = true;
      submitBtn.textContent = "Submitting...";

      try {
        const res = await fetch("/api/feedback", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await res.json();

        if (res.ok && data.success) {
          status.textContent = "Thank you. Your report has been submitted.";
          status.className = "feedback-status success";
          form.reset();
          setTimeout(close, 1000);
        } else {
          status.textContent = data.error || "Could not submit feedback. Please try again.";
          status.className = "feedback-status error";
        }
      } catch (err) {
        status.textContent = "Network error. Please try again.";
        status.className = "feedback-status error";
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = "Submit";
      }
    });
  }

  document.addEventListener("DOMContentLoaded", buildWidget);
})();
