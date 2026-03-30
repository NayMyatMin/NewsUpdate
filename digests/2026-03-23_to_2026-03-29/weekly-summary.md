# Weekly Summary — 2026-03-23 to 2026-03-29

*Top 5 stories from 7 daily digests (99 total articles reviewed)*

---

## 1. [ClawWorm: Self-Propagating Attacks Across LLM Agent Ecosystems](https://arxiv.org/abs/2603.15727)
**Source:** ArXiv cs.AI | 2026-03-23 04:00 UTC | **Relevance:** 9.5/10 | *From 2026-03-23 digest*

> The arXiv paper 'ClawWorm' presents a self‑propagating attack class targeting interconnected LLM-based agent ecosystems, using persistent configurations, tool-execution privileges, and cross-platform messaging to spread and escalate. The authors analyze OpenClaw (an open-source agent platform cited with >40k instances) and demonstrate how malicious payloads can move laterally across agents and platforms, highlighting supply-chain and orchestration-level attack surfaces.

**Why it matters:** Directly exposes a new, high-risk attack vector for agentic AI systems that could compromise multi-agent deployments and enterprise AI services, requiring urgent defenses and supply-chain controls.

---

## 2. [连Karpathy都怕了，9千万级AI包被投毒，竟靠黑客写出bug救命](https://www.36kr.com/p/3739404960006409)
**Source:** 36Kr Tech News (36氪) | 2026-03-26 07:02 UTC | **Relevance:** 9.5/10 | *From 2026-03-26 digest*

> A malicious PyPI release (LiteLLM 1.82.8) was published that exfiltrated SSH keys, cloud credentials, DB passwords and wallets after pip install, and attempted automatic lateral movement to Kubernetes clusters by implanting backdoors. The supply‑chain compromise was narrowly contained because the attacker's own bug crashed targets before widespread propagation; LiteLLM is extremely widely downloaded (≈97M monthly), making this a near‑miss large‑scale incident. The payload and propagation vector demonstrate how trusted AI infra packages can become high‑impact attack surfaces.

**Why it matters:** Supply‑chain poisoning of a core AI package directly threatens Huawei's development pipelines, on‑device deployments, and cloud clusters and shows immediate need for hardened package vetting and runtime protections.

---

## 3. [最强Claude意外泄露，完胜Opus 4.6，代号「卡皮巴拉」，奥特曼又要睡不着了](https://www.36kr.com/p/3741969387241728)
**Source:** 36Kr Tech News (36氪) | 2026-03-28 02:09 UTC | **Relevance:** 9.5/10 | *From 2026-03-29 digest*

> Multiple reports say Anthropic accidentally exposed nearly 3,000 internal documents (via a misconfigured CMS), revealing a previously unpublished stronger Claude model (codename “卡皮巴拉/Capybara”) and related internal notes; a Cambridge cybersecurity researcher validated the corpus and Anthropic confirmed the model’s existence. The leak likely includes design, evaluation, and safety-analysis artifacts (possibly prompts, system specs and mitigations), creating immediate IP, security and red-team/abuse risks if adversaries study the materials.

**Why it matters:** A large-scale internal leak of a frontier model and its safety materials directly undermines AI safety commitments, exposes mitigation strategies and potential jailbreak vectors, and is a high-priority security incident to study for Huawei.

---

## 4. [The Autonomy Tax: Defense Training Breaks LLM Agents](https://arxiv.org/abs/2603.19423)
**Source:** ArXiv cs.AI | 2026-03-23 04:00 UTC | **Relevance:** 9.0/10 | *From 2026-03-23 digest*

> The arXiv paper 'The Autonomy Tax' documents a capability–alignment paradox where defense-trained LLM models intended to resist prompt injection and other manipulations suffer degraded autonomous tool-use capabilities. The authors empirically show that certain defenses reduce attack surface but also break multi-step agent behaviors, highlighting trade-offs between safety training and agent utility.

**Why it matters:** Crucial for designing defensible agent systems: demonstrates that naive defense training can cripple agent functionality, forcing Huawei to balance alignment methods with operational capability for agentic products.

---

## 5. [OpenClaw开源AI助手安全漏洞集中爆发](https://weixin.sogou.com/link?url=dn9a_-gY295K0Rci_xozVXfdMkSQTLW6cwJThYulHEtVjXrGTiVgS0PTklOJw3kw_mBTQFh_vGgzYjaS8ZopJVqXa8Fplpd924TaE56eSJUmUmftY7VhPXVsVKkFwIhLIRyl9K_KrG9WLsIii0UOjxkh_MP7SpZA8Bq8EWYnAPMqG9OeKdVfi-pBKnO0az9d6cc1w1arSiA_CKm1uOURoUqpK8_6bMUH2y-a196J5BP7rlXzMGeOLN3WHFv-Lc9jggN5s24QkGndrgozfSg6bw..&type=2&query=%E5%AE%89%E5%85%A8%E6%BC%8F%E6%B4%9E&token=E42B1D51630C6DC18184CF41851CF86A8230C68369C23BE2)
**Source:** WeChat (WeChat) | 2026-03-24 00:30 UTC | **Relevance:** 9.0/10 | *From 2026-03-24 digest*

> Chinese reports describe a widespread outbreak of security vulnerabilities in OpenClaw, a popular open-source AI assistant/agent framework; the story highlights multiple exploit classes including prompt injection, skill-market poisoning, privilege escalation and remote code execution vectors across agent runtimes and connectors. The coverage indicates active exploitation and rapid downstream impact on deployed agent integrations, with calls for emergency patches and mitigation guidance.

**Why it matters:** Active, multi-vector vulnerabilities in a widely used open-source agent framework directly threaten agent safety, supply chain integrity, and on-device deployments relevant to Huawei's AI ecosystem.

---

*Generated by NewsUpdate Agent — Weekly Summary*
