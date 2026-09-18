---
hide:
  - toc
---

<style>
.main-wrapper {
  display: flex;
  gap: 1.5rem;
  max-width: 1200px;
  margin: 0 auto;
  align-items: stretch;
}

@media (max-width: 768px) {
  .main-wrapper {
    flex-direction: column;
  }
  .side-card {
    display: none !important;
  }
}

.hero-container {
  flex: 2;
  padding: 3rem 1.5rem;
  background: var(--md-default-bg-color);
  border-radius: 1.25rem;
  box-shadow: 0 4px 20px rgba(0,0,0,0.05);
  border: 1px solid rgba(0, 188, 212, 0.2);
  text-align: center;
}

.side-card {
  flex: 1;
  padding: 2rem;
  background: var(--md-default-bg-color);
  border-radius: 1.25rem;
  box-shadow: 0 4px 20px rgba(0,0,0,0.05);
  border: 1px solid rgba(0, 188, 212, 0.2);
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 2rem;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  text-align: left;
}

.feature-icon {
  flex-shrink: 0;
  width: 50px;
  height: 50px;
  color: #00bcd4;
}

.feature-icon svg {
  width: 100%;
  height: 100%;
  fill: currentColor;
}

.feature-content h3 {
  margin: 0 0 0.25rem 0;
  font-size: 1.25rem;
  font-weight: 800;
  text-transform: uppercase;
  color: var(--md-default-fg-color);
  letter-spacing: 0.5px;
}

.feature-content p {
  margin: 0;
  font-size: 1rem;
  color: var(--md-default-fg-color--light);
  line-height: 1.4;
}

.full-width-card {
  width: 100%;
  padding: 3rem 1.5rem;
  background: var(--md-default-bg-color);
  border-radius: 1.25rem;
  box-shadow: 0 4px 20px rgba(0,0,0,0.05);
  border: 1px solid rgba(0, 188, 212, 0.2);
  text-align: center;
  margin-top: 0.5rem;
}

html[data-md-color-scheme="slate"] .hero-container,
html[data-md-color-scheme="slate"] .side-card,
html[data-md-color-scheme="slate"] .full-width-card {
  background: var(--md-default-bg-color);
  box-shadow: 0 4px 20px rgba(0,0,0,0.25);
  border: 1px solid rgba(0, 188, 212, 0.4);
}

.hero-container h1 {
  font-size: 2.5rem;
  font-weight: 800;
  margin-bottom: 1rem;
  color: var(--md-default-fg-color);
}

.hero-container h1 span.bd-accent {
  color: #00bcd4;
}

.hero-container p.subtitle {
  font-size: 1.2rem;
  color: var(--md-default-fg-color--light);
  margin-bottom: 2rem;
  line-height: 1.6;
}

.side-card h3 {
  margin-top: 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--md-default-fg-color);
}

.side-card p {
  color: var(--md-default-fg-color--light);
  font-size: 1rem;
  line-height: 1.5;
}

.btn-primary {
  display: inline-block;
  background-color: #00bcd4;
  color: #fff !important;
  text-decoration: none;
  padding: 0.8rem 1.5rem;
  border-radius: 999px;
  font-weight: 700;
  font-size: 1rem;
  transition: filter 0.2s, transform 0.2s;
  margin-top: 1rem;
  white-space: nowrap;
}

.btn-primary:hover {
  filter: brightness(1.1);
  transform: translateY(-2px);
}

.full-width-card h2 {
  margin-top: 0;
  font-size: 2rem;
  font-weight: 800;
  color: var(--md-default-fg-color);
  margin-bottom: 1rem;
}

.full-width-card p {
  color: var(--md-default-fg-color--light);
  font-size: 1.2rem;
  line-height: 1.6;
  max-width: 800px;
  margin: 0 auto;
}

.mini-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1.5rem;
  margin-top: 3rem;
  text-align: left;
}

.mini-card {
  padding: 1.5rem;
  border-radius: 0.75rem;
  background: var(--md-default-bg-color);
  border: 1px solid rgba(0, 188, 212, 0.15);
  box-shadow: 0 2px 10px rgba(0,0,0,0.02);
  transition: border-color 0.3s ease, transform 0.3s ease;
  display: flex;
  flex-direction: column;
  container-type: inline-size;
}

.mini-card:hover {
  border-color: #00bcd4;
  transform: translateY(-3px);
}

.mini-card h3 {
  margin-top: 0;
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--md-default-fg-color);
  margin-bottom: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.mini-card p {
  font-size: 0.95rem;
  line-height: 1.5;
  color: var(--md-default-fg-color--light);
  margin: 0;
}

.mini-card .btn-primary {
  align-self: center;
  width: auto;
  min-width: 140px;
  margin: 2rem auto 0 auto;
}

.get-started-card {
  scroll-margin-top: 7rem;
  padding: 3.5rem 2rem;
  overflow: hidden;
}

.get-started-header {
  max-width: 760px;
  margin: 0 auto;
  text-align: center;
}

.get-started-kicker {
  display: inline-flex;
  align-items: center;
  padding: 0.35rem 0.7rem;
  margin-bottom: 0.9rem;
  border: 1px solid rgba(0, 188, 212, 0.35);
  border-radius: 999px;
  color: #00bcd4;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.get-started-header h2 {
  margin-bottom: 0.65rem;
  font-size: clamp(2rem, 4vw, 2.75rem);
}

.get-started-header p {
  max-width: 620px;
  font-size: 1.05rem;
}

.get-started-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.65fr) minmax(250px, 0.85fr);
  gap: 1.5rem;
  margin-top: 2.5rem;
  text-align: left;
}

.get-started-primary {
  position: relative;
  padding: 2rem;
  border: 1px solid rgba(0, 188, 212, 0.42);
  border-radius: 1rem;
  background:
    radial-gradient(700px 220px at 0% 0%, rgba(0, 188, 212, 0.13), transparent 60%),
    var(--md-default-bg-color);
}

html[data-md-color-scheme="slate"] .get-started-primary {
  background:
    radial-gradient(700px 220px at 0% 0%, rgba(0, 188, 212, 0.12), transparent 60%),
    rgba(255,255,255,0.015);
}

.get-started-badge {
  display: inline-flex;
  align-items: center;
  margin-bottom: 1.25rem;
  padding: 0.28rem 0.62rem;
  border-radius: 999px;
  background: rgba(0, 188, 212, 0.12);
  color: #00bcd4;
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.get-started-primary h3,
.get-started-option h3 {
  margin: 0 0 0.6rem;
  color: var(--md-default-fg-color);
  font-weight: 800;
}

.get-started-primary h3 {
  font-size: 1.55rem;
}

.get-started-primary p,
.get-started-option p {
  max-width: none;
  margin: 0;
  color: var(--md-default-fg-color--light);
  font-size: 0.95rem;
  line-height: 1.55;
}

.get-started-terminal {
  margin-top: 1.5rem;
  overflow: hidden;
  border: 1px solid rgba(255,255,255,0.10);
  border-radius: 0.75rem;
  background: #161821;
  box-shadow: 0 10px 30px rgba(0,0,0,0.12);
}

.get-started-terminal-bar {
  display: flex;
  align-items: center;
  gap: 0.38rem;
  padding: 0.65rem 0.8rem;
  border-bottom: 1px solid rgba(255,255,255,0.08);
  color: #8f95b2;
  font-size: 0.72rem;
}

.get-started-terminal-dot {
  width: 0.48rem;
  height: 0.48rem;
  border-radius: 50%;
  background: #4b5065;
}

.get-started-terminal-label {
  margin-left: 0.35rem;
  font-family: monospace;
}

.get-started-terminal-code {
  display: block;
  padding: 1rem 1.1rem 1.15rem;
  overflow-x: auto;
  color: #d6d9e8;
  font-family: monospace;
  font-size: clamp(0.76rem, 1.6vw, 0.9rem);
  line-height: 1.75;
  white-space: nowrap;
}

.get-started-terminal-prompt {
  color: #00bcd4;
  user-select: none;
}

.get-started-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.9rem;
  margin-top: 1.4rem;
}

.get-started-actions .btn-primary {
  margin: 0;
}

.get-started-note {
  color: var(--md-default-fg-color--light);
  font-size: 0.8rem;
}

.get-started-secondary {
  display: grid;
  grid-template-rows: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.get-started-option {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 1.4rem;
  border: 1px solid rgba(0, 188, 212, 0.16);
  border-radius: 0.9rem;
  background: var(--md-default-bg-color);
}

.get-started-option h3 {
  font-size: 1.05rem;
}

.get-started-status {
  align-self: flex-start;
  margin-top: 1rem;
  padding: 0.28rem 0.6rem;
  border-radius: 999px;
  background: var(--md-code-bg-color);
  color: var(--md-default-fg-color--light);
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

@media (max-width: 800px) {
  .get-started-card {
    padding: 2.5rem 1.25rem;
  }

  .get-started-layout {
    grid-template-columns: 1fr;
  }

  .get-started-secondary {
    grid-template-columns: 1fr 1fr;
    grid-template-rows: none;
  }
}

@media (max-width: 560px) {
  .get-started-primary {
    padding: 1.35rem;
  }

  .get-started-secondary {
    grid-template-columns: 1fr;
  }

  .get-started-actions {
    align-items: stretch;
  }

  .get-started-actions .btn-primary {
    width: 100%;
    text-align: center;
  }
}
</style>

<div class="main-wrapper" style="flex-wrap: wrap;">
  <div class="hero-container">
    <a href="https://youtu.be/98zhTFi2I14" target="_blank" rel="noopener noreferrer" style="display: block; width: 100%; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.15); transition: transform 0.2s;">
      <img src="https://img.youtube.com/vi/98zhTFi2I14/maxresdefault.jpg" alt="OntoBDC Video" style="width: 100%; height: auto; display: block;">
    </a>
  </div>

  <div class="side-card">
    <div style="display: flex; flex-direction: column; align-items: center; text-align: center; margin-bottom: 1.5rem; padding-bottom: 1.5rem;">
      <img src="https://raw.githubusercontent.com/OntoBDC/ontobdc-doc/master/content/assets/images/ontobdc-logo.png" data-i18n="site.logo_alt" data-i18n-attr="alt" alt="OntoBDC Logo" style="max-height: 64px; margin-bottom: 0.75rem;">
      <h2 style="margin: 0; font-size: 1.5rem;">Onto<span class="bd-accent" data-i18n="hero.title_accent">BDC</span></h2>
      <p style="font-size: 0.85rem; margin-top: 0.5rem; line-height: 1.4;">
        <strong style="color: var(--md-default-fg-color);" data-i18n="hero.strong_subtitle">Ontology-Based Datasets & Containers</strong><br /><br />
        <span style="display: block; margin-top: 0.25rem; color: var(--md-default-fg-color--light);" data-i18n="hero.soft_subtitle">A unified standard to define, distribute, and orchestrate open data datasets through code.</span>
      </p>
    </div>
  </div>

  <div class="full-width-card">
    <h2 data-i18n="capabilities.title">Do everything with capabilities</h2>
    <p data-i18n="capabilities.description">These are small executable scripts embedded directly within the "digital briefcase" (the .obdc pointer) that teach any computer or system on the network how to read, transform, or validate that specific dataset.</p>

    <div class="mini-cards-grid">
      <div class="mini-card">
        <h3 data-i18n="capabilities.card1_title">🛡️ Data Sovereignty</h3>
        <p data-i18n="capabilities.card1_desc">Validate engineering projects locally (Edge Execution). Eliminate costly proprietary licenses and orchestrate sensitive data without transferring it to third-party infrastructures.</p>
      </div>
      <div class="mini-card">
        <h3 data-i18n="capabilities.card2_title">⏳ Future-Proof</h3>
        <p data-i18n="capabilities.card2_desc">Project data must last decades. OntoBDC ensures your data and inspection tools can be reproduced identically 20 years from now, immunizing your organization against software obsolescence.</p>
      </div>
      <div class="mini-card">
        <h3 data-i18n="capabilities.card3_title">🤖 AI-Ready</h3>
        <p data-i18n="capabilities.card3_desc">Using the container manifest as a structured guide, LLMs can autonomously trigger capabilities with less hallucinations, enabling advanced auditing without sending IP to Big Tech clouds.</p>
      </div>
    </div>
  </div>

  <div class="full-width-card" style="margin-top: 1.5rem; background: var(--md-code-bg-color); border: none;">
    <h2 data-i18n="ownership.title">Your data is your data</h2>
    <p data-i18n="ownership.description">OntoBDC embraces true open data principles. You retain full ownership, control, and accessibility of your engineering data without being tied to proprietary formats or vendor lock-in.</p>

    <div class="mini-cards-grid">
      <div class="mini-card">
        <h3 data-i18n="ownership.card1_title">🎯 Single Source of Truth</h3>
        <p data-i18n="ownership.card1_desc">You define the ultimate reference. Consolidate your engineering data into a single, reliable semantic model that governs all project rules and information.</p>
      </div>
      <div class="mini-card">
        <h3 data-i18n="ownership.card2_title">🔄 Seamless Synchronization</h3>
        <p data-i18n="ownership.card2_desc">Keep data flowing perfectly. Automatically synchronize information across multiple .obdc containers and integrate effortlessly with third-party systems.</p>
      </div>
      <div class="mini-card">
        <h3 data-i18n="ownership.card3_title">🔌 Offline Local Execution</h3>
        <p data-i18n="ownership.card3_desc">Work without limits. Process, validate, and query your complex data entirely offline, right on your machine, with zero dependency on internet connections.</p>
      </div>
    </div>
  </div>

  <div class="full-width-card get-started-card" id="get_started" style="margin-top: 1.5rem;">
    <div class="get-started-header">
      <span class="get-started-kicker">Start here</span>
      <h2 data-i18n="get_started.title">Get Started</h2>
      <p data-i18n="get_started.description">Install OntoBDC locally, verify the CLI, and then move into the documentation when you are ready to build your first workflow.</p>
    </div>

    <div class="get-started-layout">
      <div class="get-started-primary">
        <span class="get-started-badge">Recommended</span>
        <h3 data-i18n="get_started.card2_title">Local CLI</h3>
        <p data-i18n="get_started.card2_desc">The fastest path to OntoBDC is the command line. Install the package with pip, confirm the installation, and open the CLI command tree.</p>

        <div class="get-started-terminal" aria-label="OntoBDC installation commands">
          <div class="get-started-terminal-bar">
            <span class="get-started-terminal-dot"></span>
            <span class="get-started-terminal-dot"></span>
            <span class="get-started-terminal-dot"></span>
            <span class="get-started-terminal-label">terminal</span>
          </div>
          <code class="get-started-terminal-code"><span class="get-started-terminal-prompt">$</span> pip install ontobdc<br><span class="get-started-terminal-prompt">$</span> ontobdc --version<br><span class="get-started-terminal-prompt">$</span> ontobdc</code>
        </div>

        <div class="get-started-actions">
          <a href="01-getting-started/" class="btn-primary" data-i18n="get_started.card2_btn">Read Documentation</a>
          <span class="get-started-note">Python package · local execution · no cloud required</span>
        </div>
      </div>

      <div class="get-started-secondary">
        <div class="get-started-option">
          <div>
            <h3 data-i18n="get_started.card1_title">Browser Runtime</h3>
            <p data-i18n="get_started.card1_desc">Run OntoBDC directly in the browser when the web runtime is available, without a local installation.</p>
          </div>
          <span class="get-started-status">Coming soon</span>
        </div>

        <div class="get-started-option">
          <div>
            <h3 data-i18n="get_started.card3_title">Google Colab</h3>
            <p data-i18n="get_started.card3_desc">Use a hosted notebook environment for experiments and remote datasets without configuring a local Python environment.</p>
          </div>
          <span class="get-started-status">Coming soon</span>
        </div>
      </div>
    </div>
  </div>
</div>
