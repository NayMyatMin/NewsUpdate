# Topic definitions with keyword clusters
# Broad tech coverage for an AI Safety Researcher at Huawei who wants
# to stay on top of ALL tech news: AI, cybersecurity, infosec, cloud, etc.

TOPICS = {
    # === HIGH PRIORITY (weight 3.0) ===
    "ai_safety": {
        "label": "AI Safety & Alignment",
        "weight": 3.0,
        "keywords_en": [
            "ai safety", "ai alignment", "ai risk", "existential risk",
            "responsible ai", "ai ethics", "ai bias", "ai fairness",
            "safe ai", "beneficial ai", "ai guardrails", "safety evaluation",
            "ai safety institute", "frontier model safety",
        ],
        "keywords_zh": [
            "AI安全", "人工智能安全", "AI对齐", "AI风险",
            "负责任AI", "AI伦理", "AI偏见", "AI公平性",
        ],
    },
    "ai_security": {
        "label": "AI Security & Attacks",
        "weight": 3.0,
        "keywords_en": [
            "ai security", "adversarial attack", "adversarial machine learning",
            "prompt injection", "jailbreak", "jailbreaking", "red teaming",
            "model extraction", "data poisoning", "backdoor attack",
            "model stealing", "membership inference", "ai vulnerability",
            "llm security", "ai threat", "training data attack",
        ],
        "keywords_zh": [
            "AI安全攻击", "对抗攻击", "对抗样本", "提示注入",
            "越狱攻击", "红队测试", "模型窃取", "数据投毒",
            "后门攻击", "大模型安全",
        ],
    },
    "huawei_ecosystem": {
        "label": "Huawei & Ecosystem",
        "weight": 3.0,
        "keywords_en": [
            "huawei", "harmonyos", "harmony os", "ascend",
            "mindspore", "kunpeng", "huawei cloud", "pangu model",
            "cann", "huawei ai", "kirin chip", "hisilicon",
        ],
        "keywords_zh": [
            "华为", "鸿蒙", "昇腾", "昇思", "鲲鹏",
            "华为云", "盘古大模型", "麒麟芯片", "海思",
        ],
    },

    # === MEDIUM-HIGH PRIORITY (weight 2.5) ===
    "llm": {
        "label": "Large Language Models",
        "weight": 2.5,
        "keywords_en": [
            "large language model", "llm", "gpt", "claude", "gemini",
            "chatgpt", "foundation model", "transformer", "fine-tuning",
            "rlhf", "instruction tuning", "context window", "tokenizer",
            "language model benchmark", "llm evaluation", "hallucination",
            "reasoning model", "chain of thought",
        ],
        "keywords_zh": [
            "大语言模型", "大模型", "基础模型", "语言模型",
            "微调", "思维链", "幻觉问题", "模型评估",
        ],
    },
    "ai_agents": {
        "label": "AI Agents",
        "weight": 2.5,
        "keywords_en": [
            "ai agent", "autonomous agent", "multi-agent", "agent framework",
            "tool use", "function calling", "agentic ai", "agent benchmark",
            "computer use agent", "coding agent", "ai assistant",
            "agent orchestration", "mcp protocol",
        ],
        "keywords_zh": [
            "AI智能体", "自主智能体", "多智能体", "智能体框架",
            "工具调用", "AI助手", "智能体编排",
        ],
    },
    "cybersecurity": {
        "label": "Cybersecurity & Incidents",
        "weight": 2.5,
        "keywords_en": [
            "data breach", "ransomware", "zero day", "zero-day", "0day",
            "vulnerability", "cve", "exploit", "malware", "phishing",
            "apt", "advanced persistent threat", "supply chain attack",
            "cybersecurity", "cyber attack", "cyberattack", "infosec",
            "threat actor", "nation state hacker", "botnet", "ddos",
            "security incident", "security breach", "hack", "hacked",
            "credential stuffing", "brute force attack",
            "security advisory", "patch tuesday", "critical vulnerability",
            "remote code execution", "rce", "privilege escalation",
            "sql injection", "xss", "cross-site scripting",
            "security flaw", "bug bounty", "penetration testing",
        ],
        "keywords_zh": [
            "数据泄露", "勒索软件", "零日漏洞", "漏洞",
            "恶意软件", "钓鱼攻击", "网络攻击", "网络安全",
            "信息安全", "安全事件", "APT攻击", "供应链攻击",
            "黑客", "安全漏洞", "渗透测试", "安全通报",
            "远程代码执行", "提权漏洞", "安全补丁",
        ],
    },
    "ai_regulation": {
        "label": "AI Governance & Regulation",
        "weight": 2.5,
        "keywords_en": [
            "ai regulation", "ai governance", "eu ai act", "ai policy",
            "ai legislation", "ai executive order", "ai standards",
            "ai compliance", "ai audit", "algorithmic accountability",
            "ai oversight", "ai transparency", "model cards",
        ],
        "keywords_zh": [
            "AI监管", "人工智能治理", "AI法规", "AI政策",
            "算法治理", "AI合规", "AI标准", "人工智能管理办法",
            "生成式人工智能", "算法备案",
        ],
    },

    # === MEDIUM PRIORITY (weight 2.0) ===
    "frontier_models": {
        "label": "Frontier & Open-Source Models",
        "weight": 2.0,
        "keywords_en": [
            "deepseek", "qwen", "llama", "mistral", "open source ai",
            "open weight", "multimodal", "vision language model",
            "text to image", "text to video", "diffusion model",
            "mixture of experts", "scaling law", "emergent abilities",
        ],
        "keywords_zh": [
            "DeepSeek", "通义千问", "开源模型", "多模态",
            "文生图", "文生视频", "扩散模型", "混合专家",
        ],
    },
    "mobile_telecom": {
        "label": "Mobile & Telecom",
        "weight": 2.0,
        "keywords_en": [
            "on-device ai", "mobile ai", "edge ai", "5g ai", "6g",
            "telecom ai", "smartphone ai", "npu", "neural processing unit",
            "apple intelligence", "samsung ai", "google pixel ai",
            "qualcomm ai", "mediatek ai", "on-device llm",
            "iphone", "android", "ios update", "mobile security",
        ],
        "keywords_zh": [
            "端侧AI", "手机AI", "边缘AI", "终端智能",
            "神经处理单元", "设备端大模型", "5G", "6G",
        ],
    },
    "geopolitical_ai": {
        "label": "Geopolitical AI & Chips",
        "weight": 2.0,
        "keywords_en": [
            "us china ai", "ai chip export", "semiconductor", "ai sanctions",
            "nvidia ban", "chip restriction", "ai competition",
            "technology decoupling", "ai sovereignty", "compute governance",
            "gpu shortage", "ai chip", "asml",
        ],
        "keywords_zh": [
            "中美AI", "芯片出口管制", "半导体", "AI制裁",
            "芯片限制", "科技脱钩", "AI主权", "算力治理",
        ],
    },
    "cybersecurity_ai": {
        "label": "AI in Cybersecurity",
        "weight": 2.0,
        "keywords_en": [
            "ai cybersecurity", "ai phishing", "deepfake", "ai malware",
            "ai social engineering", "ai scam", "synthetic media",
            "voice cloning", "ai fraud", "ai-generated attack",
            "cybersecurity automation", "ai threat detection",
        ],
        "keywords_zh": [
            "AI网络安全", "AI钓鱼", "深度伪造", "AI恶意软件",
            "AI诈骗", "合成媒体", "语音克隆", "AI威胁检测",
        ],
    },
    "cloud_infra": {
        "label": "Cloud & Infrastructure",
        "weight": 2.0,
        "keywords_en": [
            "cloud computing", "aws", "azure", "google cloud", "gcp",
            "kubernetes", "docker", "serverless", "microservices",
            "cloud security", "cloud breach", "saas", "paas", "iaas",
            "devops", "devsecops", "ci/cd", "infrastructure as code",
            "cloud native", "service mesh", "cloud outage",
        ],
        "keywords_zh": [
            "云计算", "云安全", "云原生", "容器化",
            "微服务", "云服务", "阿里云", "腾讯云", "百度云",
        ],
    },
    "privacy_data": {
        "label": "Privacy & Data Protection",
        "weight": 2.0,
        "keywords_en": [
            "data privacy", "gdpr", "data protection", "privacy law",
            "surveillance", "facial recognition ban", "biometric",
            "end-to-end encryption", "privacy breach", "pii",
            "data sovereignty", "cross-border data",
        ],
        "keywords_zh": [
            "数据隐私", "个人信息保护", "隐私保护", "数据安全法",
            "个人信息保护法", "数据出境", "人脸识别", "生物识别",
        ],
    },

    # === STANDARD PRIORITY (weight 1.5) ===
    "software_dev": {
        "label": "Software & Developer Tools",
        "weight": 1.5,
        "keywords_en": [
            "github", "gitlab", "programming language", "rust lang",
            "python release", "javascript", "typescript", "golang",
            "developer tools", "ide", "vscode", "copilot",
            "open source", "linux kernel", "software supply chain",
            "package manager", "npm", "pip", "cargo",
            "webassembly", "wasm", "api design", "graphql",
        ],
        "keywords_zh": [
            "开发者工具", "编程语言", "开源软件", "软件开发",
            "代码托管", "技术栈", "前端框架", "后端框架",
        ],
    },
    "blockchain_web3": {
        "label": "Blockchain & Web3",
        "weight": 1.5,
        "keywords_en": [
            "blockchain", "cryptocurrency", "bitcoin", "ethereum",
            "smart contract", "defi", "nft", "web3",
            "crypto hack", "crypto regulation", "cbdc",
            "digital currency",
        ],
        "keywords_zh": [
            "区块链", "加密货币", "比特币", "以太坊",
            "智能合约", "数字货币", "数字人民币", "Web3",
        ],
    },
    "quantum_computing": {
        "label": "Quantum Computing",
        "weight": 1.5,
        "keywords_en": [
            "quantum computing", "quantum computer", "qubit",
            "quantum supremacy", "quantum advantage", "quantum error correction",
            "post-quantum cryptography", "quantum encryption",
            "quantum threat", "quantum resistant",
        ],
        "keywords_zh": [
            "量子计算", "量子计算机", "量子比特", "量子霸权",
            "后量子密码", "量子加密", "量子通信",
        ],
    },
    "robotics_hardware": {
        "label": "Robotics & Hardware",
        "weight": 1.5,
        "keywords_en": [
            "robotics", "autonomous vehicle", "self-driving",
            "humanoid robot", "drone", "chip design", "gpu",
            "tpu", "nvidia", "amd", "intel", "tsmc",
            "risc-v", "arm chip", "neuromorphic",
        ],
        "keywords_zh": [
            "机器人", "自动驾驶", "无人机", "芯片设计",
            "人形机器人", "具身智能", "算力",
        ],
    },
    "tech_business": {
        "label": "Big Tech & Business",
        "weight": 1.5,
        "keywords_en": [
            "google", "microsoft", "apple", "amazon", "meta",
            "openai", "anthropic", "nvidia earnings",
            "tech layoff", "tech acquisition", "ipo",
            "antitrust", "tech monopoly", "startup funding",
        ],
        "keywords_zh": [
            "谷歌", "微软", "苹果", "亚马逊",
            "科技裁员", "科技并购", "融资", "上市",
            "反垄断", "科技巨头", "互联网公司",
        ],
    },
}


def get_all_keywords() -> dict[str, list[str]]:
    """Return all keywords grouped by language."""
    en_keywords = []
    zh_keywords = []
    for topic in TOPICS.values():
        en_keywords.extend(topic["keywords_en"])
        zh_keywords.extend(topic["keywords_zh"])
    return {"en": en_keywords, "zh": zh_keywords}


def match_topics(text: str) -> list[str]:
    """Return list of topic IDs that match the given text."""
    text_lower = text.lower()
    matched = []
    for topic_id, topic in TOPICS.items():
        for kw in topic["keywords_en"]:
            if kw.lower() in text_lower:
                matched.append(topic_id)
                break
        else:
            for kw in topic["keywords_zh"]:
                if kw in text:
                    matched.append(topic_id)
                    break
    return matched


def relevance_score(topic_ids: list[str]) -> float:
    """Calculate a weighted relevance score from matched topic IDs."""
    return sum(TOPICS[tid]["weight"] for tid in topic_ids if tid in TOPICS)
