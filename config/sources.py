"""
News source registry — broad tech coverage.
AI, cybersecurity, infosec, cloud, dev tools, hardware, general tech.
"""

# ============================================================
# Google News RSS search queries
# ============================================================
GOOGLE_NEWS_QUERIES = [
    # --- English: AI ---
    {"query": "AI safety OR AI alignment OR responsible AI", "lang": "en"},
    {"query": "AI security OR adversarial attack OR prompt injection OR jailbreak", "lang": "en"},
    {"query": "large language model OR LLM OR GPT OR Claude OR Gemini", "lang": "en"},
    {"query": "AI agent OR autonomous agent OR agentic AI", "lang": "en"},
    {"query": "AI regulation OR AI governance OR EU AI Act", "lang": "en"},
    {"query": "Huawei AI OR HarmonyOS OR Ascend chip", "lang": "en"},
    {"query": "AI chip export OR semiconductor OR US China AI", "lang": "en"},
    {"query": "deepfake OR AI cybersecurity OR AI malware", "lang": "en"},
    {"query": "DeepSeek OR Qwen OR open source AI model", "lang": "en"},
    {"query": "on-device AI OR mobile AI OR edge AI", "lang": "en"},
    # --- English: Cybersecurity & Infosec ---
    {"query": "data breach OR ransomware attack OR zero day exploit", "lang": "en"},
    {"query": "cybersecurity incident OR critical vulnerability OR CVE", "lang": "en"},
    {"query": "supply chain attack OR APT OR nation state hacker", "lang": "en"},
    # --- English: General tech ---
    {"query": "cloud computing OR kubernetes OR serverless", "lang": "en"},
    {"query": "quantum computing OR post-quantum cryptography", "lang": "en"},
    {"query": "robotics OR humanoid robot OR autonomous vehicle", "lang": "en"},

    # --- Chinese: AI ---
    {"query": "AI安全 OR 人工智能安全 OR AI对齐", "lang": "zh"},
    {"query": "大语言模型 OR 大模型 OR AI智能体", "lang": "zh"},
    {"query": "华为 AI OR 鸿蒙 OR 昇腾", "lang": "zh"},
    {"query": "芯片出口管制 OR 半导体 OR 中美AI", "lang": "zh"},
    {"query": "AI监管 OR AI治理 OR 生成式人工智能", "lang": "zh"},
    # --- Chinese: Cybersecurity ---
    {"query": "网络安全 OR 数据泄露 OR 勒索软件", "lang": "zh"},
    {"query": "安全漏洞 OR 零日漏洞 OR 黑客攻击", "lang": "zh"},
    {"query": "信息安全 OR 供应链攻击 OR 安全事件", "lang": "zh"},
    # --- Chinese: General tech ---
    {"query": "云计算 OR 云安全 OR 云原生", "lang": "zh"},
    {"query": "量子计算 OR 区块链 OR 数字货币", "lang": "zh"},
    {"query": "自动驾驶 OR 机器人 OR 芯片设计", "lang": "zh"},
    {"query": "科技公司 OR 互联网 OR 开源软件", "lang": "zh"},
]

# ============================================================
# Direct RSS feeds
# ============================================================
RSS_FEEDS = [
    # === AI & ML ===
    {"url": "https://techcrunch.com/category/artificial-intelligence/feed/", "source": "TechCrunch AI", "lang": "en"},
    {"url": "https://www.wired.com/feed/tag/ai/latest/rss", "source": "Wired AI", "lang": "en"},
    {"url": "https://www.technologyreview.com/feed/", "source": "MIT Tech Review", "lang": "en"},
    {"url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "source": "The Verge AI", "lang": "en"},
    {"url": "http://export.arxiv.org/rss/cs.AI", "source": "ArXiv cs.AI", "lang": "en"},
    {"url": "http://export.arxiv.org/rss/cs.CR", "source": "ArXiv cs.CR", "lang": "en"},
    {"url": "http://export.arxiv.org/rss/cs.CL", "source": "ArXiv cs.CL", "lang": "en"},
    {"url": "https://blog.google/technology/ai/rss/", "source": "Google AI Blog", "lang": "en"},
    {"url": "https://openai.com/blog/rss.xml", "source": "OpenAI Blog", "lang": "en"},
    {"url": "https://huggingface.co/blog/feed.xml", "source": "Hugging Face Blog", "lang": "en"},
    {"url": "https://www.deepmind.com/blog/rss.xml", "source": "DeepMind Blog", "lang": "en"},
    {"url": "https://engineering.fb.com/category/ml-applications/feed/", "source": "Meta Engineering ML", "lang": "en"},
    {"url": "https://machinelearning.apple.com/rss.xml", "source": "Apple ML Blog", "lang": "en"},
    {"url": "https://blogs.microsoft.com/ai/feed/", "source": "Microsoft AI Blog", "lang": "en"},
    {"url": "https://lilianweng.github.io/index.xml", "source": "Lil'Log (Lilian Weng)", "lang": "en"},
    {"url": "https://newsletter.ruder.io/feed", "source": "NLP Newsletter (Ruder)", "lang": "en"},
    {"url": "https://thesequence.substack.com/feed", "source": "The Sequence", "lang": "en"},
    {"url": "https://jack-clark.net/feed/", "source": "Import AI (Jack Clark)", "lang": "en"},

    # === Major news outlets ===
    {"url": "https://feeds.bbci.co.uk/news/technology/rss.xml", "source": "BBC Tech", "lang": "en"},
    {"url": "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml", "source": "NYT Tech", "lang": "en"},
    {"url": "https://feeds.arstechnica.com/arstechnica/technology-lab", "source": "Ars Technica", "lang": "en"},

    # === Cybersecurity & Infosec ===
    {"url": "https://krebsonsecurity.com/feed/", "source": "Krebs on Security", "lang": "en"},
    {"url": "https://www.schneier.com/feed/", "source": "Schneier on Security", "lang": "en"},
    {"url": "https://thehackernews.com/feeds/posts/default", "source": "The Hacker News", "lang": "en"},
    {"url": "https://www.bleepingcomputer.com/feed/", "source": "BleepingComputer", "lang": "en"},
    {"url": "https://www.darkreading.com/rss.xml", "source": "Dark Reading", "lang": "en"},
    {"url": "https://www.securityweek.com/feed/", "source": "SecurityWeek", "lang": "en"},
    {"url": "https://feeds.feedburner.com/TheHackersNews", "source": "Hacker News (Security)", "lang": "en"},
    {"url": "https://threatpost.com/feed/", "source": "Threatpost", "lang": "en"},
    {"url": "https://www.cisa.gov/news.xml", "source": "CISA News", "lang": "en"},
    {"url": "https://nvd.nist.gov/feeds/xml/cve/misc/nvd-rss.xml", "source": "NIST NVD", "lang": "en"},
    {"url": "https://blog.talosintelligence.com/rss/", "source": "Cisco Talos", "lang": "en"},
    {"url": "https://www.mandiant.com/resources/blog/rss.xml", "source": "Mandiant Blog", "lang": "en"},
    {"url": "https://securelist.com/feed/", "source": "Securelist (Kaspersky)", "lang": "en"},
    {"url": "https://unit42.paloaltonetworks.com/feed/", "source": "Unit 42 (Palo Alto)", "lang": "en"},
    {"url": "https://www.sentinelone.com/labs/feed/", "source": "SentinelOne Labs", "lang": "en"},
    {"url": "https://blog.cloudflare.com/rss/", "source": "Cloudflare Blog", "lang": "en"},
    {"url": "https://portswigger.net/research/rss", "source": "PortSwigger Research", "lang": "en"},
    {"url": "https://googleprojectzero.blogspot.com/feeds/posts/default", "source": "Google Project Zero", "lang": "en"},

    # === Chinese cybersecurity (direct RSS) ===
    {"url": "https://www.freebuf.com/feed", "source": "FreeBuf (安全)", "lang": "zh"},
    {"url": "https://paper.seebug.org/rss/", "source": "Seebug Paper", "lang": "zh"},
    {"url": "https://xz.aliyun.com/feed", "source": "Xianzi (先知社区)", "lang": "zh"},

    # === General tech / Dev ===
    {"url": "https://hnrss.org/frontpage", "source": "Hacker News (YC)", "lang": "en"},
    {"url": "https://lobste.rs/rss", "source": "Lobsters", "lang": "en"},
    {"url": "https://www.infoq.com/feed/", "source": "InfoQ", "lang": "en"},
    {"url": "https://github.blog/feed/", "source": "GitHub Blog", "lang": "en"},
    {"url": "https://devblogs.microsoft.com/devops/feed/", "source": "MS DevOps Blog", "lang": "en"},
    {"url": "https://blog.golang.org/feed.atom", "source": "Go Blog", "lang": "en"},
    {"url": "https://blog.rust-lang.org/feed.xml", "source": "Rust Blog", "lang": "en"},

    # === Cloud & Infrastructure ===
    {"url": "https://aws.amazon.com/blogs/aws/feed/", "source": "AWS Blog", "lang": "en"},
    {"url": "https://cloud.google.com/blog/rss", "source": "Google Cloud Blog", "lang": "en"},
    {"url": "https://azure.microsoft.com/en-us/blog/feed/", "source": "Azure Blog", "lang": "en"},
    {"url": "https://kubernetes.io/feed.xml", "source": "Kubernetes Blog", "lang": "en"},

    # === Chinese general tech ===
    {"url": "https://www.infoq.cn/feed", "source": "InfoQ China", "lang": "zh"},
]

# ============================================================
# RSSHub routes — Chinese platform coverage
# RSSHub converts walled-garden platforms to standard RSS.
# Works with public instances or self-hosted (set RSSHUB_BASE_URL).
# ============================================================
RSSHUB_ROUTES = [
    # --- News & Finance ---
    {"route": "/cls/telegraph", "source": "CLS Telegraph (财联社)", "lang": "zh"},
    {"route": "/36kr/newsflashes", "source": "36Kr Newsflash (36氪快讯)", "lang": "zh"},
    {"route": "/36kr/information/web_news", "source": "36Kr Tech News (36氪)", "lang": "zh"},
    {"route": "/thepaper/channel/25950", "source": "The Paper Tech (澎湃科技)", "lang": "zh"},

    # --- AI & Tech communities ---
    {"route": "/zhihu/hotlist", "source": "Zhihu Hot (知乎热榜)", "lang": "zh"},
    {"route": "/zhihu/topic/19551275", "source": "Zhihu AI Topic (知乎AI)", "lang": "zh"},
    {"route": "/v2ex/topics/latest", "source": "V2EX Latest", "lang": "zh"},
    {"route": "/jiqizhixin/daily", "source": "Synced/Jiqizhixin (机器之心)", "lang": "zh"},
    {"route": "/leiphone/category/ai", "source": "Leiphone AI (雷锋网AI)", "lang": "zh"},

    # --- Cybersecurity ---
    {"route": "/anquanke/category/web安全", "source": "Anquanke (安全客)", "lang": "zh"},
    {"route": "/hackernews/best", "source": "HN Best Stories", "lang": "en"},

    # --- Video/Social platforms (tech channels) ---
    {"route": "/bilibili/ranking/technology/0/3", "source": "Bilibili Tech (B站科技)", "lang": "zh"},
    {"route": "/weibo/keyword/AI安全", "source": "Weibo #AI安全#", "lang": "zh"},
    {"route": "/weibo/keyword/网络安全", "source": "Weibo #网络安全#", "lang": "zh"},
]

# ============================================================
# WeChat search queries (Sogou scraper)
# ============================================================
WECHAT_SEARCH_QUERIES = [
    # AI
    "AI安全",
    "大模型安全",
    "人工智能治理",
    "华为AI",
    "AI智能体",
    "大语言模型",
    "AI芯片",
    "深度伪造",
    # Cybersecurity
    "网络安全事件",
    "数据泄露",
    "勒索软件攻击",
    "安全漏洞",
    # General tech
    "云计算",
    "量子计算",
    "自动驾驶",
    "科技新闻",
]
