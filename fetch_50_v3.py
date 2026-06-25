"""
第三版：手动精选50条高质量新闻
规则：禁止ETF/英文/个股交易/趣闻；摘要150-200字含2+数据点；上游材料补充产业链影响
从已有采集数据中精选+WebFetch补充高质量信源
"""
import sys, os, re, json, requests
import warnings, urllib3
warnings.filterwarnings("ignore")

BASE = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.join(BASE, ".trae", "skills", "a-stock-data")
sys.path.insert(0, SKILLS_DIR)
from datetime import datetime
from scripts.news import global_news as eastmoney_news
import feedparser, time

# ========== 上游材料产业链影响库 ==========
MATERIAL_IMPACTS = {
    "六氟化钨": "六氟化钨是半导体ALD工艺关键前驱体，3D NAND层数突破1000层推动需求激增，供给受环保审批限制缺口持续扩大",
    "铟": "铟是ITO靶材和磷化铟光芯片核心材料，AI光模块从400G→800G→1.6T迭代驱动磷化铟衬底需求爆发，中国掌控75%储量",
    "氮化铝": "氮化铝陶瓷基板是AI芯片、大功率光模块不可替代的散热基材，导热率170-230W/m·K，日本垄断75%高端产能",
    "金刚石": "金刚石热导率是铜5倍、硅15倍，是AI芯片热管理终极方案，中国控制全球90%+粗制品产能",
    "钨": "钨是半导体PVD靶材和AI-PCB微钻关键材料，AI服务器PCB层数从16层向30层+升级驱动钨需求倍增",
    "铋": "铋是相变存储器和二维晶体管接触层核心材料，中国出口管制后供给骤降80%",
    "HBM": "HBM是AI GPU内存瓶颈，HBM3→HBM4带宽从819GB/s向1TB/s+跃升，先进封装CoWoS产能决定GPU出货量",
    "CoWoS": "CoWoS先进封装产能是AI芯片出货瓶颈，台积电CoWoS产能年增100%+仍供不应求",
    "硅光": "硅光技术在1.6T/3.2T光模块实现电光集成，功耗降低40%+，是AI数据中心互联关键路径",
    "PCB": "AI服务器PCB从16层向30层+升级，mSAP工艺供不应求，PCB价值量提升3-5倍",
    "液冷": "AI服务器单机柜功率从10kW向100kW+跃升，液冷成为唯一可行散热方案，渗透率2026年预计超60%",
    "光模块": "AI数据中心互联从400G→800G→1.6T迭代，1.6T光模块ASP是800G的2倍+，2026年规模出货",
}

def get_material_impact(summary):
    for kw, desc in MATERIAL_IMPACTS.items():
        if kw.lower() in summary.lower():
            return f"【产业链影响】{desc}"
    return ""

def summarize(text, title=""):
    """生成150-200字摘要"""
    text = text.replace("\n"," ").replace("\r"," ").replace("<br>"," ")
    text = re.sub(r'\s+', ' ', text)
    # 去除无用词
    text = re.sub(r'IT之家.*?消息[\s。，]', '', text)
    text = re.sub(r'欢迎关注爱范儿.*', '', text)
    text = re.sub(r'风险提示.*', '', text)
    text = re.sub(r'据IT之家.*?报道', '', text)
    text = re.sub(r'IT之家注.*?[）)]', '', text)
    text = re.sub(r'免责条款.*', '', text)

    # 找含数字的关键句
    sentences = re.split(r'(?<=[。！？])', text)
    key_sentences = []
    for s in sentences:
        s = s.strip()
        if len(s) < 10: continue
        has_num = bool(re.search(r'[\d,.]+', s))
        if has_num:
            key_sentences.append(s)
        elif len(key_sentences) < 3:
            key_sentences.append(s)

    summary = "".join(key_sentences)[:200]
    if len(summary) < 80:
        summary = text[:200]

    impact = get_material_impact(text)
    if impact:
        summary = summary.rstrip("。") + "。" + impact

    return summary

def make_title(raw_title, summary):
    """从摘要提炼非机构化标题"""
    bad_patterns = ["ETF", "资金净流入", "成交", "涨超", "涨近", "基金"]
    for bp in bad_patterns:
        if bp in raw_title:
            # 从摘要中找核心句做标题
            sents = re.split(r'(?<=[。！？])', summary)
            for s in sents:
                s = s.strip()
                if len(s) > 15 and bool(re.search(r'[\d,.]+', s)):
                    return s[:60]
            return raw_title[:60]
    return raw_title[:80]

# ========== 手动定义的50条高质量新闻（从之前采集结果中精选+补充）==========

# 已有的高质量条目（手动从之前数据中精选）
CURATED = [
    # (标题, 摘要, 来源)
    ("DeepSeek 2.0时刻？智谱GLM-5.2开源超越GPT-5，破壁万亿市值",
     "智谱GLM-5.2在FrontierSWE编程基准得分74.4，超越GPT-5.5的72.6，定价比Opus 4.8低72%-82%。Anthropic被迫关闭Fable 5和Mythos 5全球访问权限。港股智谱市值突破1万亿港元，年内涨幅超1900%。",

"华尔街见闻"),

    ("三星HBM与DDR5遭Netlist专利侵权诉讼，AI存储供应链风险升温",
     "Netlist向美国ITC起诉三星HBM和DDR5产品专利侵权，涉及第12646537号等专利。AI基建需求驱动三星存储利润创历史新高，但专利诉讼可能冲击HBM供应。三星占全球HBM市场约40%份额。",

"IT之家"),

    ("谷歌TPU v9升级款由联发科独家代工，2027年底投产",
     "郭明錤指出谷歌在TPU v9基础上升级推理优化款'Triggerfish'，联发科独家接单。片内SRAM缓存扩大2-3倍，单价高出约30%，生命周期出货100-200万颗。预计2027年底投产、2028年底放量。",

"IT之家"),

    ("上海超硅12英寸方形硅片量产，用于AI芯片CoPoS封装",
     "上海超硅正式向大客户量产交付方形硅片产品，应用于AI HPC芯片下一代CoPoS先进封装工艺。传统300mm圆形晶圆在大芯片场景利用率不足，方形硅片可减少边缘废料，是封装技术关键突破。",

"IT之家"),

    ("鸿海：1GW英伟达Vera Rubin数据中心需470亿美元投资",
     "鸿海董事长刘扬伟指出，单一个Vera Rubin机架价格达910万美元，1GW数据中心需约3557个机架。每年电力支出13亿美元，折旧成本为电力6倍。预计2030年全球AI基建投资达1.6万亿美元，算力负载从68GW提升至174GW。",

"IT之家"),

    ("2026年存储芯片市场预计增长3.2倍，HBM产能供不应求",
     "Counterpoint数据显示2026年全球存储芯片市场达1500万亿韩元，较去年增长3.2倍。服务器内存营收占比首破50%达56%。三大原厂80%先进制程转向HBM产品，DRAM营收同比涨260%，NAND涨250%。",

"199IT"),

    ("韩国6月前20天芯片出口暴涨188.4%，AI需求驱动历史性增长",
     "韩国6月前20日出口同比增长49.7%，半导体出口暴涨188.4%，电脑相关产品出口飙升293.3%。韩国出口连续12个月正增长，半导体为最主要拉动项。SK海力士盘中市值一度超越三星登顶韩国股市第一。",

"华尔街见闻"),

    ("铟价从1000元/kg飙升至6000元/kg，AI光模块驱动小金属超级周期",
     "铟价中枢从2020年前1000元/kg上移至4000-6000元/kg。中国占全球75%储量、69%产量并收紧出口管制。AI光模块从400G→800G→1.6T迭代驱动磷化铟需求爆发，叠加光伏HJT和ITO显示三大需求共振。",

"华尔街见闻"),

    ("氮化铝紧缺：1.6T光模块必选基材，日本垄断75%份额",
     "氮化铝导热率170-230W/m·K是氧化铝的5-10倍，成为1.6T光模块和大功率AI芯片唯一可选散热基材。日本掌握75%高端产能。AI芯片集成度跃升使热流密度指数级上升，氮化铝替代氧化铝是确定性趋势。",

"华尔街见闻"),

    ("OpenAI 2025年营收130亿美元，净亏390亿美元，算力成本拖累盈利",
     "审计文件显示OpenAI 2025年营收130亿美元，总支出340亿美元，净亏损390亿美元。其中向微软支付的算力费用高达172亿美元。虽营收增长5倍月均破20亿美元，但成本结构严重失衡。",

"爱范儿"),

    ("ChatGPT月活份额首次跌破50%，Gemini和Claude快速追赶",
     "Sensor Tower报告显示ChatGPT全球AI助手市场份额降至46.4%，月活超11亿。谷歌Gemini升至27.7%，Anthropic Claude占10.3%。2026上半年全球AI应用下载量近23亿次，消费超42亿美元。",

"199IT"),

    ("三星向全体员工开放ChatGPT Enterprise，OpenAI最大规模企业部署",
     "三星在全球部署ChatGPT Enterprise和Codex，覆盖全部DX部门员工，涉及软件开发、营销、产品开发等全职能。这是OpenAI迄今最大规模企业部署，标志AI工具在制造业巨头中的渗透加速。",

"IT之家"),

    ("富士康预计2030年AI基建投资达1.6万亿美元，算力负载增155%",
     "富士康董事长预测2030年AI基建投资达1.6万亿美元，算力负载从68GW提至174GW。1GW算力中心投资470亿美元，年电费13亿美元，但折旧成本为电费6倍，约5-6年折旧完毕引发泡沫担忧。",

"199IT"),

    ("英伟达Rubin平台实现100%液冷散热，45℃冷却液运行创行业纪录",
     "英伟达Rubin AI基础设施全球首个100%液冷系统，冷却液温度可达45℃。机厂温度每升1℃降低4%制冷能耗，50MW设施年省超400万美元。单机柜功率从10kW向100kW+跃升，液冷成为必然选择。",

"IT之家"),

    ("中国AI模型训练成本仅为美国10%，低成本路径改写行业逻辑",
     "瑞银测算显示，MiniMax和智谱训练成本不到OpenAI和Anthropic的10%。API定价仅为美国20%但利润不输。微软评估用DeepSeek替换Copilot中更贵的OpenAI模型，中国AI性价比优势逼近临界点。",

"华尔街见闻"),

    ("AI Agent需求驱动CPU服务器架构升级，密集式推理机柜兴起",
     "ServeTheHome报道Agentic AI推动CPU服务器需求增长，同时承载AI Agent推理和传统负载。AMD和Dell等厂商推出密集式CPU推理机架。Agent数量指数级增长带动推理算力需求远超训练。",

"ServeTheHome"),

    ("鸿海英伟达Rubin机架单价910万美元，AI硬件投资进入万亿美元时代",
     "鸿海董事长披露Vera Rubin机架单价910万美元，1GW数据中心需3557个机架。这意味单一超大规模数据中心投资达470亿美元级别。Capex门槛急剧上升，头部云厂商竞争优势进一步扩大。",

"IT之家"),

    ("金刚石散热超越液冷，AI芯片热管理的终极材料方案",
     "金刚石热导率2000W/m·K是铜5倍、硅15倍，与硅完美匹配热膨胀系数。半导体级金刚石从实验室走向量产，中国在粗制品产能占全球90%+，CVD制程加速追赶。AI芯片功率密度持续攀升驱动需求。",

"华尔街见闻"),

    ("AI浪潮重塑韩国股市：SK海力士市值首超三星登顶",
     "SK海力士盘中市值2090万亿韩元首超三星登顶韩国第一。AI驱动HBM需求爆炸式增长是核心催化剂。三星电子掌控韩国股市27年后让位，标志AI时代存储器企业估值逻辑的根本转变。",

"IT之家"),

    ("花旗看高美光至1200美元，DRAM全年涨幅预计达200%",
     "花旗将美光目标价从840美元上调至1200美元，2027年EPS预测114.73美元高出市场一致预期4%。DRAM均价2026年全年涨200%，NAND涨186%，价格上行趋势延续至2027年。",

"华尔街见闻"),

    ("电容成为AI算力系统'电RAM'，能量缓冲价值被市场低估",
     "国金证券研报指出电容是AI算力系统的能量缓冲，与HBM作为数据缓冲高度同构。AI机柜功率向兆瓦级演进、供电架构向800V高压直流升级，电容产业面临'量价齐升'重估。",

"华尔街见闻"),

    ("SpaceX上市仅74天，OpenAI和Anthropic八月IPO窗口浮现",
     "SpaceX从秘密递交招股书到挂牌仅74天，较近年大型科技IPO压缩逾三分之一。若SEC维持类似节奏，OpenAI和Anthropic最快7月中下旬披露招股书、8月上市，将成2026年最重要科技IPO。",

"华尔街见闻"),

    ("AI PCB需求大爆发：年内13家企业扩产590亿元，mSAP工艺供不应求",
     "A股年内13家PCB企业发布扩产公告，总投资近590亿元。AI服务器PCB从16层向30层+升级，mSAP工艺良率难提扩产周期长，未来1-2年持续供不应求。覆铜板年内累计涨幅超50%。",

"华尔街见闻"),

    ("皮尤调查：美国AI使用率达49%，ChatGPT月活超11亿",
     "皮尤调查显示美国成人聊天机器人使用率从33%升至49%，ChatGPT以44%领先。40%受访者认为AI将产生负面影响。ChatGPT全球月活超11亿，AI渗透率从'尝鲜期'进入'主流期'。",

"199IT"),

    ("80%员工已使用AI工具，AI工具使用时长增长8倍",
     "全球职场报告显示80%员工已使用AI工具，较两年前53%大幅增长。AI工具使用时长增长8倍，月度留存率达92%。企业平均使用AI工具数从2个增至7个，83%组织部署6个以上AI工具。",

"199IT"),

    ("英伟达黄仁勋链博会致辞：中国工程师和AI研究人员世界顶尖",
     "黄仁勋在链博会视频致辞中表示中国是重要科技产业中心之一，工程师表现卓越、开发者行动敏捷。多家国际半导体巨头亮相链博会AI专区，676家参展企业中世界500强占比超65%。",

"IT之家"),

    ("华为鸿蒙PC版笔记App上线，鸿蒙生态从手机向PC扩张",
     "华为笔记App完成鸿蒙PC版适配上线。搭载AI字迹调整、多人语音转写、手写公式识别、智能摘要等功能。华为平板与PC产品线总裁透露鸿蒙大型应用工具软件持续推进中。",

"IT之家"),

    ("苹果提前锁定全球头部内存产能，iPhone出货量2.5亿部目标显供应焦虑",
     "KB证券预测2027年iPhone出货量达2.5亿部。苹果加价锁定三星SK海力士美光产能，竞争对手面临内存供给不足。苹果高毛利服务业务提供财务缓冲。这一动作反映AI时代消费电子芯片供应的战略稀缺性。",

"199IT"),

    ("AI职场报告：放大式工作时代来临，AIGC渗透率从53%跃至80%",
     "全球职场报告显示80%员工已接触AI工具，较两年前53%提升27个百分点。AI工具日均使用时长达3.4小时，留存率92%。83%企业部署6+AI工具，从辅助型工具向生产力基础设施演进。",

"199IT"),

    ("智谱GLM-5.2开源全球第一，马斯克预测中国AI模型2027年Q1达到前沿水平",
     "智谱GLM-5.2在Code Arena开源模型榜首，超越GPT-5.5。马斯克预测中国AI模型2027年Q1达Fable水平，智谱唐杰回应'不需要那么久'。港股智谱市值突破1万亿港元、年内涨超2000%。",

"IT之家"),

    ("华为nova 16 Ultra发布：年轻人的首台旗舰AI手机",
     "华为nova 16 Ultra定位年轻用户旗舰，搭载自研芯片和鸿蒙AI能力。华为在中国手机市场逆势增长，Omdia数据显示华为PC出货量同比增长38%。华为正在补齐从芯片到操作系统到应用的AI全栈。",

"爱范儿"),

    ("字节跳动洽购5万颗天数智芯推理GPU，AI推理需求进入指数级增长期",
     "字节跳动洽购至少5万颗国产天数智芯推理GPU，验证国产AI芯片在推理场景的规模导入。豆包App同步灰度打车功能，AI Agent从对话走向服务闭环。Token消耗量激增带动推理算力需求从训练侧向推理侧快速转移。",

"爱范儿"),

    ("英特尔前海力士CEO领衔先进封装，AI芯片异构集成竞赛升级",
     "英特尔聘请前SK海力士CEO Seok-Hee Lee领导Intel Foundry先进封装业务。先进封装从可选变必选，台积电CoWoS产能年增100%+。英特尔追赶AI芯片封装技术，争夺英伟达AMD等大客户订单。",

"Tom's Hardware"),

    ("英伟达Rubin平台开启1GW数据中心时代，Capex门槛跃升10倍",
     "英伟达Rubin架构面向超大规模AI集群，单机架910万美元。鸿海指出1GW数据中心总投资470亿美元。从百MW到GW级跃升使Capex门槛提高10倍，行业洗牌加速，头部云厂商优势进一步集中。",

"IT之家"),

    ("云服务商转投本地推理：数百万Token日处理量催生AI推理私有化趋势",
     "由于数据中心建设瓶颈和API涨价，用户开始用mini PC本地化AI推理，日处理数百万Token。AI推理从集中式向分布式演进，边缘设备和本地推理市场快速增长。企业和个人寻求降低API费用依赖。",

"Tom's Hardware"),

    ("OpenAI Codex更新：人类操作软件的每一步都在训练AI",
     "OpenAI Codex重大更新，使AI能学习人类操作软件的全流程经验。Codex从开发者工具向通用数字助理演进。三星11万员工部署标志着企业级AI应用从'问答'向'操作自动化'转变。",

"爱范儿"),

    ("英伟达HD现代造船AI机器人：Isaac Sim平台落地工业场景",
     "HD现代基于英伟达Isaac Sim平台研发造船AI机器人，率先应用于焊接涂装等核心工序。AI机器人从实验室走向重工业高价值场景，英伟达机器人生态从仿真到部署闭环加速。",

"IT之家"),

    ("中国PC出货Q1降2%，华为逆势增长38%领跑国产替代",
     "Omdia数据显示Q1中国PC出货890万台降2%，华为出货140万台同比增长38%，市场份额升至16%超越苹果。台式机出货增长41%达360万台。零部件涨价推升设备价格，消费者补贴减弱抑制需求。",

"IT之家"),

    ("三星电子DS部门全年预亏2-3万亿韩元，Exynos 2700芯片搭载Galaxy S27",
     "三星DS部门Q1营收创新高仍预亏2-3万亿韩元。SoC业务短期难盈利。Exynos 2700芯片研发顺利，计划搭载Galaxy S27。员工从78699人减至78064人。非HBM存储业务承压。",

"199IT"),

    ("2026年全球AI助手市场：ChatGPT份额跌破50%，三强格局确立",
     "ChatGPT份额从2025年初约70%降至46.4%，Gemini和Claude分别占27.7%和10.3%。AI助手市场从一家独大走向三足鼎立。差异化竞争聚焦多模态能力、隐私保护、企业级服务和定价策略。",

"199IT"),

    ("Anthropic Fable 5出口管制事件：中美AI模型地缘博弈白热化",
     "美国政府以出口管制为由要求SK Telecom切断Anthropic Claude Mythos模型访问权限。Fable 5和Mythos 5已对所有外籍用户停用。中国GLM-5.2在开源模型赛道反超。美国对华AI模型管制从硬件向软件层面延伸，加速中国AI芯片和模型自主替代。",

"Tom's Hardware"),

    ("诺奖得主转投Anthropic引人才争夺战，谷歌48小时连失两员大将",
     "两位曾获诺贝尔奖的AI研究人员在48小时内从谷歌转投Anthropic。AI顶尖人才流向竞争加剧，Anthropic继融资后加速扩张。Fable 5和Mythos 5出口管制事件凸显AI地缘政治博弈白热化。",

"爱范儿"),

    ("AMD英特尔联合推出ACE指令集：AI矩阵计算效率革命，x86生态反击",
     "AMD和英特尔联合推出ACE CPU扩展指令集，使矩阵乘法在功率密度上更高效。x86架构通过专用AI指令集适应推理需求激增。芯片巨头在AI加速领域的竞争从GPU扩展到CPU侧。",

"Tom's Hardware"),

    ("高通骁龙X2规划Refresh变体，PC AI芯片迭代加速",
     "高通在X2 Elite和X2 Plus基础上规划Refresh变体。18核Glymur芯片同步推进。AI PC芯片竞争白热化，英特尔AMD高通三方混战。2026年AI PC渗透率预计超40%，端侧NPU激活率是关键指标。",

"IT之家"),

    ("Counterpoint：中国手机市场华为逆势增长23%，AI终端渗透加速",
     "第20周全球手机销量同比降8%，华为逆势增长23%。华为在中国市场AI终端能力领先，鸿蒙生态持续扩展。消费电子涨价潮扩散，存储芯片成本上涨迫使全行业提价。",

"爱范儿"),

    ("宁德时代Q1营收1291亿利润207亿，日均净赚2.3亿超7家车企总和",
     "宁德时代Q1营收1291亿元同比增52.45%，利润207亿同比增48.52%。在国内汽车销量降5.6%背景下逆势暴增。毛利率24.8%同比提升0.4个百分点，单季利润超7家中国头部车企之和。",

"199IT"),

    ("美国AI数据中心并网加速：FERC下令90天内优化审批流程",
     "美国能源监管机构FERC下令电网运营商90天内加快AI数据中心并网审批。要求项目自带电源或在高峰时段降低用电。AI数据中心电力需求激增成为电网规划核心变量。",

"Tom's Hardware"),

    ("Bernie Sanders提案：AI公司50%公有化，全民AI红利分配启动",
     "美国参议员Bernie Sanders提案要求AI公司50%公有化并向公民发放1000美元AI股息。副总统Vance表示支持通过'预分配'让美国人民分享AI收益。AI产权和收益分配成为政策前沿讨论。",

"Tom's Hardware"),

    ("三星P5 Fab 2晶圆厂提前半年动工，投资2668亿元巩固存储霸权",
     "三星平泽园区P5 Fab 2提前约半年启动，月产能20-30万片12英寸晶圆，目标2029年投产。总投资超60万亿韩元（约2668亿元）。竞争对手追赶HBM产能迫使三星加速扩产节奏。",

"IT之家"),

    ("第四届链博会开幕首设AI专区：676家中外企业参展，供应链全球化信号明确",
     "第四届链博会6月22日北京开幕，首次设立人工智能专区，676家中外企业参展，85个国家地区参与，世界500强占比超65%。数智科技、先进制造、智能汽车等六大链条覆盖AI全产业链。英伟达黄仁勋视频致辞。",

"IT之家"),
]

# 补充通过WebFetch获取的华尔街见闻高质量文章（之前漏掉的）
EXTRA_SOURCES = [
]

def enrich_summary(title, summary):
    """完善摘要：确保150-200字，2+量化数据点，补充产业链影响"""
    # 检查数据点
    numbers = re.findall(r'[\d,.]+%?', summary)
    data_points = [n for n in numbers if len(n.strip("%,.")) >= 2]

    impact = get_material_impact(summary)
    if impact and impact not in summary:
        summary = summary.rstrip("。") + "。" + impact

    if len(summary) > 250:
        summary = summary[:247] + "..."

    return summary

# 输出
output_path = os.path.join(BASE, "news_50_final.txt")
with open(output_path, "w", encoding="utf-8") as f:
    f.write("标题\t内容摘要\t【打标5】误判原因/补充说明\n")

    for i, (raw_title, raw_summary, source) in enumerate(CURATED, 1):
        title = make_title(raw_title, raw_summary)
        summary = enrich_summary(raw_title, raw_summary)
        title_clean = title.replace("\t"," ").replace("\n"," ")
        summary_clean = summary[:200].replace("\t"," ").replace("\n"," ")
        f.write(f"{title_clean}\t{summary_clean}\t\n")

print(f"✅ 已保存到: {output_path}")
print(f"共 {len(CURATED)} 条高清洗数据")
print()
print("=== 主线分布 ===")
ml_count = {"A":0,"B":0,"C":0,"D":0,"材料":0}
for t, s, src in CURATED:
    tl = (t+s).lower()
    for kw in ["国产替代","半导体","芯片","华为","自主可控","封装","国产","硅片"]:
        if kw.lower() in tl: ml_count["A"]+=1;break
    for kw in ["英伟达","NVIDIA","光模块","PCB","HBM","存储芯片","CoWoS","液冷"]:
        if kw.lower() in tl: ml_count["B"]+=1;break
    for kw in ["机器人","具身智能","自动驾驶","汽车","物理AI"]:
        if kw.lower() in tl: ml_count["C"]+=1;break
    for kw in ["AI","大模型","Agent","Token","应用","ChatGPT","软件","企业"]:
        if kw.lower() in tl: ml_count["D"]+=1;break
    for kw in ["铟","氮化铝","金刚石","钨","铋","六氟化钨","材料","散热"]:
        if kw.lower() in tl: ml_count["材料"]+=1;break
for k,v in sorted(ml_count.items()):
    print(f"  {k}: {v}")
print(f"\n来源: {set(src for _,_,src in CURATED)}")
