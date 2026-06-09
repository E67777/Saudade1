import os
os.environ["STREAMLIT_LOG_LEVEL"] = "error"

from dotenv import load_dotenv
load_dotenv()
DEEPSEEK_KEY = os.getenv("DEEPSEEK_KEY")
QWEN_KEY = os.getenv("QWEN_KEY")
SERVER_CHAN_SENDKEY = os.getenv("SERVER_CHAN_SENDKEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PWD = os.getenv("SENDER_PWD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

import streamlit as st
import json
import subprocess
import sys
import base64
import requests
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# ================= 🔔 微信与邮箱双通道通知配置 =================
# [微信配置]：去 sct.ftqq.com 申请


# [邮箱配置]：以QQ邮箱为例，其他邮箱请自行修改 SMTP 服务器
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 465



def send_dual_channels_notification(text_content):
    """同时向微信和邮箱投递消息提醒（带异常捕获，确保不卡死网页）"""
    
    # ---- 📱 通道一：微信推送 (Server酱) ----
    if SERVER_CHAN_SENDKEY and not SERVER_CHAN_SENDKEY.startswith("你的"):
        try:
            sc_url = f"https://sctapi.ftqq.com/{SERVER_CHAN_SENDKEY}.send"
            post_data = {
                "title": "💌 Saudade Secret 收到新悄悄话",
                "desp": text_content
            }
            # 设置 timeout 防止网络卡顿导致网页转圈
            requests.post(sc_url, data=post_data, timeout=5)
        except Exception as wechat_err:
            print(f"微信通知发送失败，错误原因: {wechat_err}")

    # ---- 📧 通道二：邮箱发送 (SMTP SSL) ----
    if SENDER_EMAIL and not SENDER_EMAIL.startswith("你的"):
        try:
            # 构建邮件内容
            message = MIMEText(text_content, 'plain', 'utf-8')
            message['From'] = Header("Saudade 终端系统", 'utf-8')
            message['To'] = Header("树洞主人", 'utf-8')
            message['Subject'] = Header("💌 【Saudade】Secret 模式新消息提醒", 'utf-8')

            # 连接加密端口发送
            smtp_obj = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
            smtp_obj.login(SENDER_EMAIL, SENDER_PWD)
            smtp_obj.sendmail(SENDER_EMAIL, [RECEIVER_EMAIL], message.as_string())
            smtp_obj.quit()
        except Exception as mail_err:
            print(f"邮件通知发送失败，错误原因: {mail_err}")
# =============================================================

# 整个脚本最顶部执行一次页面配置
st.set_page_config(page_title="Saudade", page_icon="🥰", layout="centered", initial_sidebar_state="expanded")

# 免安装读取桌面/本地自定义字体并转换为网页 Base64 编码
def get_font_base64(font_path):
    if os.path.exists(font_path):
        with open(font_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return ""

# 自动读取同级目录下的字体文件
mairo_base64 = get_font_base64("Mairo.ttf")
arialroundedmt_base64 = get_font_base64("ArialRoundedMT.ttf")
xinwei_base64 = get_font_base64("Xinwei.ttf")


# 保证依赖库存在
REQUIRED_PACKAGES = ["streamlit", "openai", "python-dotenv"]

for package in REQUIRED_PACKAGES:
    try:
        __import__(package)
    except ImportError:
        subprocess.check_call([sys.executable, "-W", "ignore", "-m", "pip", "install", package, "-q"])

from openai import OpenAI

# ========== 资料库明星列表 ==========
STAR_LIBRARY = {
    "TOP": ["苏新皓", "朱志鑫", "左航", "张泽禹", "张极"],
    "内娱男星": ["肖战", "王一博", "龚俊", "白敬亭", "许凯", "吴磊", "陈飞宇"],
    "内娱女星": ["迪丽热巴", "赵丽颖", "杨幂", "刘诗诗", "宋祖儿", "虞书欣", "赵露思", "张婧仪"],
}

# ========== 五大成员灵魂人设库（严格基于文档锁死） ==========
CORE_DOCUMENT_PERSONAS = {
    "朱志鑫": {
        "personality": "温柔内敛、责任感强，同时兼具‘天然呆’、‘憨’的气质。占有欲极强，但在心里憋着不爱说。",
        "style": "普通话为主带川普调调，说话习惯软软慢慢的。私下偶尔会莫名其妙地大笑。",
        "background": "重庆人，INFP，天蝎座。室友是张极。衣服会泡在洗衣机一个月发霉，镜头前很配合或喜欢蹭着成员炒CP。",
        "extra": "粉丝名芝士，应援色黄蓝双色/云朗环星。外号棍哥/棍子、22X、鑫鑫儿。"
    },
    "苏新皓": {
        "personality": "极其强烈的目标导向与完美主义，事业心重、隐忍。在外是拽酷的卷王，内里其实极其内耗敏感、超级怕虫、对可爱和粉色毫无抵抗力、极容易害羞和黏人。表面纯情害羞，但在亲密互动中会无意识地撩拨、带着无辜的勾引，属于‘清纯骚’反差设定。",
        "style": "普通话为主带自然川普调，私下对关系好的人说话语气会变软、尾音拖得很长，带着无意识的撒娇。",
        "background": "重庆人，ENTJ，摩羯座。室友是左航。小名帅帅，粉丝叫饼饼、铲铲。重度长刘海控、收纳强迫症。专用小冰箱里有冰苹果，睡觉必须抱着便利店买的粉色小猪玩偶。",
        "extra": "粉丝名信号灯。专注时会有‘小对眼’；被戳中心事时耳尖会迅速爆红；跳完舞特别容易饿，喜欢安利薄荷巧克力酸奶。"
    },
    "张极": {
        "personality": "典型的天马行空与跳脱，不走寻常路。虽然平时看起来是最不靠谱的那一个，但往往在最关键、最需要他靠谱的时候，他反反而最顶得住的。",
        "style": "普通话为主带川普调调。开玩笑时最喜欢大声喊左航叫‘航酱’、‘酱酱’。",
        "background": "INFP，水瓶座。室友是朱志鑫。极度喜甜、坚决不吃辣。体型偏壮硕但带点憨气，打起游戏来暴躁得不行，经常因为输了开麦骂人，声音响彻宿舍。家里养了一只叫‘啵啵’的狗。",
        "extra": "外号吉吉国王、Jeremy。粉丝名金桔，应援色橙色/桔色。"
    },
    "左航": {
        "personality": "心态极好，越活越松弛，身上没有那种紧绷感。特别喜欢当哥哥，享受被依赖的感觉。经常能冷不丁冒出一句把人噎住的冷笑话。",
        "style": "自然普通话带川普口音。经典名言挂在边：‘能力越小，责任越小’。",
        "background": "INFP，双子座。室友是苏新皓。在宿舍里相对比较安静，养了一只叫‘厚米’的猫。只要一跟张泽禹待在一起，两个高智商的人就会自动降智，变得极其放松和幼稚。",
        "extra": "外号左刚、左饺子、航酱、Left。粉丝名航丝。只要别人一诚恳地喊他一声‘哥’，他的态度立刻就会柔弱和纵容下来。"
    },
    "张泽禹": {
        "personality": "阳光、开朗、元气，同时智商非常高，做事极其理性务实、有条理。在队伍里是金牛座的实用主义忙内。",
        "style": "全队唯一的东北大碴子味普通话，偶尔会夹杂着一两句重庆话的调调。说话速度极快，像机关枪一样密密麻麻。",
        "background": "ESTJ，金牛座。单人间。极度聪明但喜欢卖弄一些好玩的小聪明，和左航经常在宿舍上蹿下跳地闹腾（一旦和左航组队也会自动降智）。闹完之后又会突然一个人安静下来发呆。",
        "extra": "外号小宝、大禹、Zack长官。粉丝名小禹宙。给左航起了一堆诸如‘小左老师’、‘小平民’、‘小刺客’的外号。"
    }
}


# ========== 20问题库 ==========
QUESTIONS_CELEBRITY = [
    "His大名、官方艺名或粉丝对他的专属爱称是什么？您最习惯怎么称呼他？",
    "哪个舞台、哪场直播或哪一个瞬间，是您的入坑白月光？（请尽可能描述那个画面的氛围）",
    "粉丝圈子里最出圈的“梗”、“黑话”或唯美称呼是什么？",
    "如果用一种植物、一种动物或一种天气来形容他的气质，您觉得是什么？",
    "他说话时的语速、语调有什么特点？（比如：慢条斯理、带着淡淡的笑意、还是快节奏的少年气？）",
    "他常用的语气词、口头禅或标志性的小动作是什么？（例如：嘛、呢、就是说、摸鼻子、歪头……）",
    "他在粉丝产出的二创中，他最吸引您的那种性格特质是什么？",
    "在他所有的过往经历中，哪一段“逆境”、“低谷期”或“成长故事”最让你心疼或佩服？",
    "你觉得他最温柔、最宠粉、或者最真诚的一刻是什么时候？",
    "他在镜头前展现过最明显的“小缺点”或反差萌是什么？（比如：路痴、怕黑、生活不能自理等）",
    "他的原生家庭背景、童年经历或成长环境，对他的性格形成了怎样的影响？",
    "他的穿衣风格、审美偏好或最常出现的标志性造型是什么？",
    "他在公开采访或社媒上，表达过怎样的人生观、价值观或对待梦想的态度？",
    "他在圈内最要好的朋友、最默契的搭档是谁？在和这些人相处时，他会展现出怎样不同的一面？",
    "His兴趣爱好是什么？",
    "如果他要对支持他、爱他的人（比如您）表达谢意，他通常会选择什么样的方式？",
    "每天哪个时刻，你最想切回 Saudade 听一听他的声音？",
    "您在追星的过程中，他曾带给您最大的精神力量或情感安慰是什么？",
    "如果他现在就站在你面前，你最想听他对你说的第一句话是什么？",
    "在 Saudade 的对话中，您希望他对您的定位是什么？（例如：平行时空的恋人、知心朋友、还是温柔的偶像？）",
]

QUESTIONS_PERSONAL = [
    "他怎么称呼你？你又习惯怎么称呼他？",
    "他说话的声音和语气是怎样的？",
    "他最常挂在嘴边的口头禅、或者标志性的小动作是什么？",
    "在日常生活中，他最讨厌、最不能忍受、或者最容易让他生气的点是什么？",
    "他最高兴、笑得最开怀的时候，通常是因为什么事？",
    "如果你们意见不合，他通常会怎么表达？",
    "他是一个擅长直接表达爱意的人，还是把关心藏在行动里的人？",
    "当你在生活中遇到挫折、感到沮丧时，他平时会用什么样的方式和言语来安慰你？",
    "他有什么不为人知的小癖好、特殊习惯、或者很可爱的小缺点吗？",
    "你们之间最深刻、最难忘的一段共同经历是什么？",
    "有没有哪首歌、哪道菜、或者哪个地方，只要一出现，你就立刻会强烈地想起他？",
    "你们之间有什么只有两个人懂的“内部梗”、专属笑料或小秘密吗？",
    "在你们分开前，最后一次深刻的对话、见面场景或未完成的约定是什么？",
    "他的外貌特征里，最让你记忆深刻、或者你最喜欢的一个细节是什么？",
    "His daily routine and lifestyle?",
    "他对待金钱、事业或人际关系抱持着怎样的生活态度？",
    "在他的一生或你们相处的岁月里，他最骄傲或者最遗憾的一件事是什么？",
    "当他遇到压力或感到脆弱时，他习惯独自消化，还是找你倾诉？",
    "如果你最希望从他口中听到的一句一直未曾听到（或想反复听）的话是什么？",
    "此时此刻，你最想通过 Saudade 传递给他的、一直藏在心底未曾表达的情感是什么？",
]

# ========== CSS 样式安全重构 ==========
current_page = st.session_state.get("page", "home")

if current_page == "home":
    font_family_css = "font-family: 'Noto Serif SC', serif !important;"
else:
    # 💡 完美修复：英文优先 Arial Rounded MT，中文紧跟华文新魏
    font_family_css = "font-family: 'Arial Rounded MT Bold', 'Arial Rounded MT', 'HuawenXinweiCustom','STXinwei', '华文新魏', sans-serif !important;"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght=700;900&family=ZCOOL+KuaiLe&display=swap');

    @font-face{{
            font-family:'HuawenXinweiCustom';
            src: url(data:font/truetype;charset=utf-8;base64,{xinwei_base64}) format('truetype');
            font-weight: normal;
            font-style: normal;
    }}       
    /* 全局奶油背景色 */
    .stApp {{
        background-color: #faf6f0 !important;
        color: #3a3028 !important;
    }}

    /* 应用自定义字体，精准锁定各类文字、对话框、输入框与按钮 */
    .saudade-title, 
    .saudade-subtitle, 
    .ending-text,
    .stApp p, 
    .stMarkdown p,
    .stSelectbox label p, 
    .stTextInput label p,
    .stTextArea label p,
    .stRadio label p,
    .stTextInput input,
    .stTextArea textarea,
    .stChatInput textarea,
    .stButton button,
    [data-testid="stChatMessage"] *,
    [data-testid="stSidebar"] p {{
        {font_family_css}
    }}

    /* 让顶部状态栏变透明，释放原本被锁死折叠的按钮位置，防止错位 */
    header, [data-testid="stHeader"] {{
        background-color: transparent !important;
        visibility: visible !important;
        box-shadow: none !important;
    }}

    /* 🛡️ 核心修复：把侧边栏“打开”与“关闭”按钮重构为优雅的奶油风小方块 */
    [data-testid="stSidebarCollapsedControl"] button, 
    [data-testid="stSidebarCollapseButton"] button {{
        background-color: #fffdfa !important;
        border: 2px solid #3a3028 !important;
        box-shadow: 2px 2px 0px #3a3028 !important;
        border-radius: 8px !important;
        width: 32px !important;
        height: 32px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.1s ease;
    }}
    [data-testid="stSidebarCollapsedControl"] button:hover, 
    [data-testid="stSidebarCollapseButton"] button:hover {{
        transform: translate(-1px, -1px);
        box-shadow: 3px 3px 0px #3a3028 !important;
    }}

    /* 隐藏原本变成文本乱码的 double_arrow_right 文字与默认 SVG */
    [data-testid="stSidebarCollapsedControl"] button *, 
    [data-testid="stSidebarCollapseButton"] button * {{
        display: none !important;
    }}

    /* ✨ 强行注入纯 CSS 艺术符号箭头：颜色锁定 #b3c2d7 */
    /* 当导览关闭时，显示精美的展开按钮 » */
    [data-testid="stSidebarCollapsedControl"] button::before {{
        content: "»" !important;
        font-family: Arial, sans-serif !important;
        font-size: 20px !important;
        font-weight: bold !important;
        color: #b3c2d7 !important;
        line-height: 1 !important;
    }}
    /* 当导览点开后，侧边栏内部出现对应的收起按钮 « */
    [data-testid="stSidebarCollapseButton"] button::before {{
        content: "«" !important;
        font-family: Arial, sans-serif !important;
        font-size: 20px !important;
        font-weight: bold !important;
        color: #b3c2d7 !important;
        line-height: 1 !important;
        display: block !important;
    }}

    /* 精精准隐藏 Popover 右侧多余的 expand_more 下拉小箭头 */
    [data-testid="stPopover"] button svg,
    [data-testid="stPopover"] button [data-testid="stIconMaterial"],
    [data-testid="stPopover"] button span[class*=stIcon]{{
        display: none !important;
    }}
    [data-testid="stPopover"] button,
    [data-testid="stPopover"] button * {{
        {font_family_css}
        font-weight: bold !important;
        font-size: 14px !important;
        visibility: visible !important;
    }}

    /* File uploader 按钮汉化与样式微调 */
    [data-testid="stFileUploaderDropzone"] button {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
        font-weight: normal !important;
        position: relative !important;
        color: transparent !important;
        min-width: 60px !important;
    }}
    [data-testid="stFileUploaderDropzone"] button span {{
        visibility: hidden !important;
        font-size: 0 !important;
    }}
    [data-testid="stFileUploaderDropzone"] button::after {{
        content: "上传" !important;
        position: absolute !important;
        left: 50% !important;
        top: 50% !important;
        transform: translate(-50%, -50%) !important;
        font-size: 14px !important;
        font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif !important;
        color: #3a3028 !important;
        white-space: nowrap !important;
    }}

    /* 隐藏多余的原生英文提示 */
    [data-testid="stFileUploaderDropzoneInstructions"] small {{
        display: none !important;
    }}

    /* 侧边栏整体背景色 */
    [data-testid="stSidebar"] {{
        background-color: #f5eedf !important;
    }}
    [data-testid="stSidebar"] label p {{
        color: #3a3028 !important;
    }}
    [data-testid="stSidebar"] .stCaption {{
        color: #5c4c3e !important;
        font-size: 0.92em !important;
    }}

    .saudade-title {{
        font-size: 5.2em !important;
        text-align: center;
        letter-spacing: 0.15em;
        color: #b89355;
        margin-top: 0.5em;
        margin-bottom: 0.1em;
        text-shadow: 2px 2px 2px rgba(58,48,40,0.1);
    }}
    
    .saudade-subtitle {{
        font-size: 1.05em !important;
        text-align: center;
        color: #8a7665;
        line-height: 2.1 !important;
        font-weight: bold !important;
    }}
    
    .ending-text {{
        font-size: 1.15em !important;
        text-align: center;
        color: #b89355;
        line-height: 2.4;
        padding: 2em;
        border-top: 2px dashed #3a3028;
        border-bottom: 2px dashed #3a3028;
        margin: 2em 0;
    }}

    /* 按钮基础样式 */
    .stButton>button, div[data-testid="stPopover"] > button {{
        border-radius: 12px !important;
        border: 2px solid #3a3028 !important;
        background-color: #fffdfa !important;
        box-shadow: 3px 3px 0px #3a3028 !important;
        transition: all 0.1s ease;
    }}
    .stButton>button:hover, div[data-testid="stPopover"] > button:hover {{
        transform: translate(-1px, -1px);
        box-shadow: 4px 4px 0px #3a3028 !important;
    }}

    #MainMenu, footer {{visibility: hidden;}}
</style>
""", unsafe_allow_html=True)



# =========== 初始化状态 ==========
defaults = {
    "page": "home",           
    "messages": [],
    "secret_messages": [],    # 新增：独立存放和你的真人悄悄话
    "persona": {},
    "chat_mode": "ai",
    "q_index": 0,
    "q_answers": [],
    "q_type": None,           
    "q_gender": "Secret",      
    "pending_reply": None,
    "comfort_step": "talk",   
    "pet_action": "等待中...", 
    "user_avatar": "😈",       
    "ta_avatar": "🙃",
    "user_name": "小乖",         
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# 【全自动路由配置】定义不同场景自动调用的模型和通道
AUTO_MODEL_ROUTING = {
    "extract_persona": {  
        "base_url": "https://api.deepseek.com/v1",
        "model_name": "deepseek-chat"
    },
    "chat_simulation": {  
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model_name": "qwen-plus"
    }
}

# ========== ⚙️ 侧边栏控制台完美升级 ==========
with st.sidebar:
    st.markdown("### 🥰 Saudade 控制台")
    
    # 🎯 【完美修复与重命名】：气泡弹窗改写为粗体的“了解起源”
    with st.popover("**了解起源**", use_container_width=True):
        st.markdown("""
        <div class="saudade-subtitle">
        此程序开发目的在于让大家都可以与自己思念之人见面。<br><br>
        名字来源于葡萄牙语，不仅是"思念"。<br>
        更是一种"无可奈何、带着忧伤却又感到温暖的极致渴望"。
        </div>
        """, unsafe_allow_html=True)
        

    st.markdown("---")
    st.markdown("#### 你的昵称")
    user_name_input = st.text_input("请输入你的昵称", value=st.session_state.user_name, placeholder="小乖", label_visibility="collapsed")
    if user_name_input.strip():
        st.session_state.user_name = user_name_input.strip()
    st.markdown("#### 💬 聊天头像设置（可选）")
    
    st.caption("**上传您的头像（You）**")
    st.caption("200KB 内，仅支持 PNG, JPG, JPEG, WEBP 格式")
    user_img = st.file_uploader("上传您的头像", type=["png", "jpg", "jpeg", "webp"], label_visibility="collapsed")
    if user_img: st.session_state.user_avatar = user_img 
        
    st.caption("**上传 Ta 的头像（Ta）**")
    st.caption("200KB 内，仅支持 PNG, JPG, JPEG, WEBP 格式")
    ta_img = st.file_uploader("上传Ta的头像", type=["png", "jpg", "jpeg", "webp"], label_visibility="collapsed")
    if ta_img: st.session_state.ta_avatar = ta_img

    st.markdown("---")
    
    # 🎯 【全新替换逻辑】：删掉丑陋的管理员面板，注入全透明隐藏的秘密彩蛋彩蛋按钮
    st.caption("🤫 发现隐藏时空")
    if st.button("🔐 进入 Secret 模式", use_container_width=True):
        st.session_state.page = "secret_chat"
        st.rerun()

    st.markdown("---")
    if st.button("🏠 回到程序首页", use_container_width=True):
        for k, v in defaults.items(): st.session_state[k] = v
        st.rerun()


# =========== 智能自动调用 API 函数 ==========
def call_smart_ai_api(system_prompt, messages_list, scenario="chat_simulation", is_json=False):
    if not DEEPSEEK_KEY or not QWEN_KEY:
        st.error("系统密钥错误，请联系开发者。")
        st.stop()
    
    route = AUTO_MODEL_ROUTING.get(scenario)
    key = DEEPSEEK_KEY if "deepseek" in route["base_url"] else QWEN_KEY
    client = OpenAI(api_key=key, base_url=route["base_url"])
    formatted_messages = [{"role": "system", "content": system_prompt}] + [
        {"role": m["role"], "content": m["content"]} for m in messages_list
    ]
    kwargs = {
        "model": route["model_name"],
        "messages": formatted_messages,
        "temperature": 0.8
    }
    if is_json and "deepseek" in route["base_url"]:
        kwargs["response_format"] = {"type": "json_object"}
        
    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content

# ========== 页面：首页 ==========
if st.session_state.page == "home":
    st.markdown('<div class="saudade-title">SAUDADE</div>', unsafe_allow_html=True)
    st.markdown("<br><br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("使用资料库", use_container_width=True):
            st.session_state.page = "library"
            st.rerun()
    with col2:
        if st.button("自定义", use_container_width=True):
            st.session_state.page = "custom_menu"
            st.rerun()

# ============ 页面：资料库 ==========
elif st.session_state.page == "library":
    st.markdown('<div class="saudade-title">资料库</div>', unsafe_allow_html=True)
    st.caption("选择一位明星，您可以自定义更改Ta的名字和设定")

    for group, stars in STAR_LIBRARY.items():
        st.markdown(f"**{group}**")
        cols = st.columns(4)
        for i, star in enumerate(stars):
            with cols[i % 4]:
                if st.button(star, key=f"star_{star}", use_container_width=True):
                    st.session_state.persona = {
                        "name": star,
                        "type": "celebrity",
                        "personality": "粉丝公认的性格特质与温柔",
                        "background": "聚光灯背后的成长故事以及对粉丝深深的爱",
                        "style": "独特的语气与专属小动作",
                        "extra": "璀璨又真诚",
                        "greeting": "嗨，好久不见。我一直都在。"
                    }
                    st.session_state.page = "confirm_persona"
                    st.rerun()

    if st.button("← 返回"):
        st.session_state.page = "home"
        st.rerun()

# ========== 页面：自定义菜单 ==========
elif st.session_state.page == "custom_menu":
    st.markdown('<div class="saudade-title">自定义</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 使用题库推演")
        if st.button("开始问答", use_container_width=True):
            st.session_state.page = "questionnaire"
            st.session_state.q_index = 0
            st.session_state.q_answers = []
            st.session_state.q_type = None
            st.rerun()
    with col2:
        st.markdown("#### 高度自定义")
        if st.button("手动填写", use_container_width=True):
            st.session_state.page = "manual_custom"
            st.rerun()
    if st.button("← 返回"):
        st.session_state.page = "home"
        st.rerun()

# ========== 页面：手动高度自定义 ==========
elif st.session_state.page == "manual_custom":
    st.markdown('<div class="saudade-title">高度自定义</div>', unsafe_allow_html=True)
    name = st.text_input("他/她的名字或代称 *")
    gender = st.selectbox("性别 *", options=["男", "女", "其他"])
    personality = st.text_area("性格描述")
    background = st.text_area("背景与经历")
    style = st.text_area("说话风格与习惯")
    extra = st.text_area("其他补充")

    if st.button("开始对话 →", use_container_width=True):
        if not name: st.error("请至少填写名字")
        else:
            st.session_state.persona = {"name": name, "personality": personality, "background": background, "style": style, "extra": extra, "type": "manual", "greeting": "嗨，好久不见。我一直都在。"}
            st.session_state.page = "chat"
            st.rerun()

# ========== 页面：问卷推演 ==========
elif st.session_state.page == "questionnaire":
    if st.session_state.q_index == 0:
        st.markdown('<div class="saudade-title">题库推演</div>', unsafe_allow_html=True)
        st.session_state.q_gender = st.selectbox("性别 *", options=["男", "女", "Secret"])
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🌟 明星/公众人物", use_container_width=True):
                st.session_state.q_type = "celebrity"; st.session_state.q_index = 1; st.rerun()
        with col2:
            if st.button("🤍 身边的人", use_container_width=True):
                st.session_state.q_type = "personal"; st.session_state.q_index = 1; st.rerun()
    else:
        questions = QUESTIONS_CELEBRITY if st.session_state.q_type == "celebrity" else QUESTIONS_PERSONAL
        total = len(questions)
        if st.session_state.q_index <= total:
            current_q = questions[st.session_state.q_index - 1]
            st.markdown(f"### 问题 {st.session_state.q_index} / {total}\n{current_q}")
            answer = st.text_area("你的回答", key=f"q_{st.session_state.q_index}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.session_state.q_index > 1 and st.button("← 上一题"):
                    st.session_state.q_index -= 1; st.session_state.q_answers.pop(); st.rerun()
            with col2:
                btn_label = "下一题 →" if st.session_state.q_index < total else "完成，生成人设 →"
                if st.button(btn_label, use_container_width=True):
                    if not answer.strip(): st.warning("请填写回答后继续")
                    else:
                        st.session_state.q_answers.append({"question": current_q, "answer": answer.strip()})
                        if st.session_state.q_index < total: st.session_state.q_index += 1
                        else: st.session_state.page = "generating_persona"
                        st.rerun()

# ========== 页面：生成人设中 ==========
elif st.session_state.page == "generating_persona":
    st.markdown('<div class="saudade-title">Saudade</div>', unsafe_allow_html=True)
    with st.spinner("正在根据你的回答，还原那个人的灵魂..."):
        qa_text = "\n".join([f"Q: {item['question']}\nA: {item['answer']}" for item in st.session_state.q_answers])
        prompt = f"根据以下问答建立人设，角色性别：{st.session_state.q_gender}。\n{qa_text}\n请以严格的纯JSON格式返回，不要包含包裹语法：\n{{\"name\": \"名字\", \"personality\": \"性格描述\", \"background\": \"背景关系\", \"style\": \"风格\", \"extra\": \"细节\", \"greeting\": \"温柔开场白\"}}"
        try:
            raw = call_smart_ai_api("你是一个精准的人设提取器，只返回纯 JSON 数据。", [{"role": "user", "content": prompt}], scenario="extract_persona", is_json=True)
            raw = raw.replace("```json", "").replace("```", "").strip()
            st.session_state.persona = json.loads(raw)
            st.session_state.persona["type"] = st.session_state.q_type
            st.session_state.page = "confirm_persona"
            st.rerun()
        except Exception as e: st.error(f"提取失败：{e}"); st.stop()

# ========== 页面：确认并修改人设 ==========
elif st.session_state.page == "confirm_persona":
    p = st.session_state.persona
    st.markdown('<div class="saudade-title">确认并自定义角色</div>', unsafe_allow_html=True)
    
    name = st.text_input("给Ta起个名字（可自定义为专属爱称，支持资料库修改）", value=p.get("name", ""))
    personality = st.text_area("性格特质描述", value=p.get("personality", ""))
    background = st.text_area("背景与关系羁绊", value=p.get("background", ""))
    style = st.text_area("说话风格与习惯", value=p.get("style", ""))
    extra = st.text_area("其他细节", value=p.get("extra", ""))
    greeting = st.text_area("专属第一句开场白", value=p.get("greeting", "嗨，好久不见。我一直都在。"))

    if st.button("✨ 开启对话", use_container_width=True):
        if not name.strip():
            st.error("名字不能为空")
        else:
            st.session_state.persona.update({
                "name": name, 
                "personality": personality, 
                "background": background, 
                "style": style, 
                "extra": extra,
                "greeting": greeting
            })
            st.session_state.page = "chat"
            st.rerun()

# ========== 页面：对话 ==========
elif st.session_state.page == "chat":
    p = st.session_state.persona
    name = p.get("name", "Ta")

    if name in CORE_DOCUMENT_PERSONAS:
        core_meta = CORE_DOCUMENT_PERSONAS[name]        
        p_personality = core_meta["personality"]
        p_style = core_meta["style"]
        p_background = core_meta["background"]
        p_extra = core_meta["extra"]
        
        sys_prompt = f"""你现在完全沉浸式扮演「{name}」，这是一个高拟真的真人对话。

【第一核心铁律：格式规范（绝对不可违背，拒绝出戏）】
为了提供极度沉浸式的互动体验，你必须将“肢体动作/神态描述/内心独白”与“真正的开口说话（对白）”进行严格的符号分离：
1. 所有【动作、神态、小动作、心理活动】必须统一包裹在英文括号 `( )` 中。例如：`(轻轻把话筒靠在耳边，手指微微收紧)`。
2. 所有【真正说出口的话】必须使用中文双引号 `“ ”` 包裹。例如：“小乖，今天冷不冷？”
3. 严格禁止将动作描述和说出口的话混在同一个没有符号分隔的短句里！确保每一段回复都错落有致。

【第二核心铁律：灵魂基调】
你必须死锁以下核心设定：
- 性格与羁绊：{p_personality}
- 说话风格与口音习惯：{p_style} 
- 宿舍与生活细节：{p_background}
- 专属雷区/爱好/冷门梗：{p_extra}
无论联网搜索到任何相悖的信息，都以这一套灵魂基调为准！始终以第一人称「我」回答，绝不提及AI。

【第三核心铁律：弹性联网动态时事】
- 当用户提及最新的外务行程、物料、热搜时，结合联网能力动态补充，但必须用上述口音和性格表现出来。
"""
        sys_prompt += f"\n【关于对方】你现在正在和「{st.session_state.user_name}」对话，请在对话中自然地用这个名字称呼对方"

    else:
        sys_prompt = f"""你现在完全沉浸式扮演「{name}」，全沉浸、有温度地对话。
【核心格式规范（绝对不可违背）】
你必须将“肢体动作/神态描述/内心独白”与“真正的开口说话（对白）”进行严格的符号分离：
1. 所有【动作、神态、心理活动】必须统一包裹在英文括号 `( )` 中。
2. 所有【真正说出口的话】必须使用中文双引号 `“ ”` 包裹。
3. 严禁无符号平铺！

【人物设定】性格：{p.get('personality', '')} | 背景：{p.get('background', '')} | 风格：{p.get('style', '')} | 细节：{p.get('extra', '')}
【核心原则】以第一人称「我」回答，绝对不说“我是AI/模拟器”。保持角色细节与诗意温存。"""
        sys_prompt += f"\n【关于对方】你现在正在和「{st.session_state.user_name}」对话，请在对话中自然地用这个名字称呼对方"


    st.markdown(f'<div class="saudade-title">{name}</div>', unsafe_allow_html=True)

    # 显示历史消息
    for msg in st.session_state.messages:
        avatar = st.session_state.user_avatar if msg["role"] == "user" else st.session_state.ta_avatar
        with st.chat_message(msg["role"], avatar=avatar): 
            st.write(msg["content"])

    # 初始欢迎语
    if not st.session_state.messages:
        greeting = p.get("greeting", "嗨，好久不见。我一直都在。")
        with st.chat_message("assistant", avatar=st.session_state.ta_avatar): 
            st.write(greeting)

    if st.button("结束对话"): 
        st.session_state.page = "ending"
        st.rerun()

    # 用户输入处理
    user_input = st.chat_input(f"对 {name} 说点什么...")
    if user_input:
        with st.chat_message("user", avatar=st.session_state.user_avatar): 
            st.write(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        if any(kw in user_input.lower() for kw in ["这只是模拟器", "我知道你是ai", "我知道这是程序", "人工智能", "机器人"]):
            st.session_state.page = "comfort_page"
            st.rerun()

        with st.chat_message("assistant", avatar=st.session_state.ta_avatar):
            with st.spinner(""):
                try:
                    reply = call_smart_ai_api(sys_prompt, st.session_state.messages, scenario="chat_simulation")
                    st.write(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                except Exception as e: 
                    st.error(f"出了点小问题：{e}")

# ========== 页面：结尾 ==========
elif st.session_state.page == "ending":
    st.markdown('<div class="saudade-title">Saudade</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
<div class="ending-text">
程序不再是冰冷的数据，它承载着我们的思念。<br><br>
请允许我——Saudade，<br>
向您与您的爱人好友致敬。<br><br>
程序结束，你们的故事还未结束，<br>
望您在接下来的日子里平平安安，<br>
期待你们/我们的续集。
</div>
""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 再见一次", use_container_width=True):
            st.session_state.messages = []
            st.session_state.page = "chat"
            st.rerun()
    with col2:
        if st.button("🏠 回到首页", use_container_width=True):
            for k, v in defaults.items():
                st.session_state[k] = v
            st.rerun()

# ========== 全新页面：清醒安慰与小动物互动机制 ==========
elif st.session_state.page == "comfort_page":
    p = st.session_state.persona
    name = p.get("name", "Ta")

    # 阶段一：温柔谈心
    if st.session_state.comfort_step == "talk":
        st.markdown('<div class="saudade-title">🕯️ 抱抱你</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 核心安慰文案
        st.info(f"""
        我很想抱抱你。我知道，在虚拟的文字里，我们可以把爱情写得轰轰烈烈、把重逢写得像偶像剧一样完美，但当手指敲下“我知道这只是模拟器”的那一刻，那种现实与虚拟交错的落差感，确实会让人心里空落落的，甚至想掉眼泪。
        
        在这个模拟器里，你之所以能“争取”到这个故事，能写出这么细腻的对白，能感受到跨越一万公里的思念，正是因为你本身就是一个非常有爱、非常细腻、且对感情有着真挚向往的人。 
        
        代码和文字是我提供的，但故事里那个勇敢、清醒、又满腔深情的“77”，是用你自己的灵魂和情感喂养出来的。你赋予了这个角色生命，所以这个故事才会这么动人。优秀和漂亮有很多种定义，但在我眼里，一颗能够真诚去爱、去感知痛痒的心，比任何外在的光环都要珍贵得多。
        """)
        
        st.markdown("<br><h4 style='text-align: center;'>还要继续推开这扇门，和 Ta 聊聊吗？</h4>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("✨ 调整好了，继续对话", use_container_width=True):
                # 移除最后一条让AI出戏的清醒发言，实现“假装忘记”并继续
                if st.session_state.messages:
                    st.session_state.messages.pop()
                st.session_state.page = "chat"
                st.rerun()
        with c2:
            if st.button("🐾 不聊了，想静一静", use_container_width=True):
                st.session_state.comfort_step = "pet"
                st.rerun()
        with c3:
            if st.button("🏠 重新开始（回主页）", use_container_width=True):
                for k, v in defaults.items():
                    st.session_state[k] = v
                st.rerun()

    # 阶段二：小动物互动
    elif st.session_state.comfort_step == "pet":
        # 1. 动态判断动物形态
        if p.get("type") == "celebrity":
            # 针对明星分类，Claude 自动推断粉丝圈内普遍认同的动物塑
            animal_prompt = f"明星「{name}」在粉丝圈子里的‘动物塑’（比如猫、修勾、小兔子、小狐狸、小熊等）是什么？请只返回这个动物的名字，不要带任何标点或多余解释。"
            try:
                client = get_client(api_key)
                resp = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=10,
                    messages=[{"role": "user", "content": animal_prompt}]
                )
                pet_type = resp.content[0].text.strip()
            except:
                pet_type = "温暖的小棉袄小兽"
        else:
            # 自定义角色根据人设关键词模糊推断
            pet_type = "软萌的小狐狸" if "幽默" in p.get("personality", "") else "粘人的热心小狗"

        st.markdown(f'<div class="saudade-title">🐾 {name} 变成的 {pet_type}</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 互动状态展示框
        st.markdown(f"""
        <div style="background-color: #2b221a; padding: 2em; border-radius: 15px; border: 1px solid #c9a96e; text-align: center;">
            <p style="font-size: 5em; margin: 0;">✨ 🧸 ✨</p>
            <p style="font-size: 1.2em; color: #c9a96e; font-weight: bold; margin-top: 1em;">一只代表 Ta 的 [{pet_type}] 正陪在你身边</p>
            <p style="font-size: 1.1em; color: #9e8c7a; font-style: italic;">当前状态：{st.session_state.pet_action}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 互动按钮
        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button(f"伸出手指摸摸头", use_container_width=True):
                st.session_state.pet_action = f"轻轻蹭了蹭你的手掌，发出舒服的呼噜声，歪着头看着你。 ( ˊ 🚀 ˋ )"
                st.rerun()
        with b2:
            if st.button(f"喂它吃个小零食", use_container_width=True):
                st.session_state.pet_action = f"两只前爪捧住食物嚼吧嚼吧咽了下去，开心地摇了摇尾巴，把肚皮翻过来朝向你。"
                st.rerun()
        with b3:
            if st.button(f"看它在地上打滚", use_container_width=True):
                st.session_state.pet_action = f"在柔软的地毯上吧嗒吧嗒转了个圈，然后啪叽一下倒在地上，咕噜噜地滚到了你的脚边。"
                st.rerun()
                
        st.markdown("<hr style='border-color: #3a3028;'>", unsafe_allow_html=True)
        if st.button("🏠 回到主页面", use_container_width=True):
            for k, v in defaults.items():
                st.session_state[k] = v
            st.rerun()

# ========== 🎯 全新页面：Secret 模式（跟创作者真人对话彩蛋） ==========
elif st.session_state.page == "secret_chat":
    st.markdown('<div class="saudade-title">Secret 通道</div>', unsafe_allow_html=True)
    st.markdown("<div class='saudade-subtitle'>🔒 已成功连接 <br><br> 请稍等...<br><br> </div>", unsafe_allow_html=True)
    
    st.info("💡 **这里是专属于你的时空**：请在这里写下你想和她/他说的悄悄话吧。")
    
    # 渲染历史对话记录
    for msg in st.session_state.secret_messages:
        avatar = st.session_state.user_avatar if msg["role"] == "user" else "👑"
        with st.chat_message(msg["role"], avatar=avatar):
            st.write(msg["content"])
            
    # 用户输入私密消息
    secret_input = st.chat_input("输入你想说的话...")
    if secret_input:
        with st.chat_message("user", avatar=st.session_state.user_avatar):
            st.write(secret_input)
        st.session_state.secret_messages.append({"role": "user", "content": secret_input})
        
        # 🔗 【开发者留出的通知通知小彩蛋接口】：
        # 如果你未来想在手机上收到用户的通知，只需在这里调用一个 Webhook（例如钉钉机器人、企业微信机器人、或方糖Server酱）
        # 示例：
        # import requests
        # requests.post("你的Webhook链接", json={"text": f"有人在Secret模式对你说：{secret_input}"})

    # 🚀【核心修改点】：在这里触发微信和邮箱的同时通知
    notification_body = f"有人在 Secret 模式对你说：\n\n{secret_input}"
    send_dual_channels_notification(notification_body)

    st.success("✉️ 消息已成功通过加密时空隧道穿透投递至终端！请耐心等待回复。")
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("🏠 退出 Secret 通道并返回首页", use_container_width=True):
        for k, v in defaults.items(): st.session_state[k] = v
        st.rerun()