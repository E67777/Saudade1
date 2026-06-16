import os
os.environ["STREAMLIT_LOG_LEVEL"] = "error"

from dotenv import load_dotenv
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_KEY")
DEEPSEEK_KEY = os.getenv("DEEPSEEK_KEY")
DOUBAO_KEY = os.getenv("DOUBAO_KEY")
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
import datetime
import hashlib
import re
from email.mime.text import MIMEText
from email.header import Header

# ================= 微信与邮箱双通道通知配置 =================
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 465



def send_dual_channels_notification(text_content):
    """同时向微信和邮箱投递消息提醒（带异常捕获，确保不卡死网页）"""
    
    # ---- 微信推送 (Server酱) ----
    if SERVER_CHAN_SENDKEY and not SERVER_CHAN_SENDKEY.startswith("你的"):
        try:
            sc_url = f"https://sctapi.ftqq.com/{SERVER_CHAN_SENDKEY}.send"
            post_data = {
                "title": "💌 Saudade Secret 收到新悄悄话",
                "desp": text_content
            }
            
            requests.post(sc_url, data=post_data, timeout=5)
        except Exception as wechat_err:
            print(f"微信通知发送失败，错误原因: {wechat_err}")

    # ---- 邮箱发送 (SMTP SSL) ----
    if SENDER_EMAIL and not SENDER_EMAIL.startswith("你的"):
        try:
            # 邮件内容
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

@st.cache_resource
def get_global_tracker():
    return {"code_usage": {}}

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False  

today_date = datetime.date.today()
today_str = today_date.strftime("%Y%m%d")

SECRET_SALT = st.secrets.get("SERVER_CHAN_SENDKEY", "SaudadeFallbackSalt")
raw_salt_string = f"{today_str}_{SECRET_SALT}"

today_code = hashlib.sha256(raw_salt_string.encode()).hexdigest()[:6].upper()

tracker = get_global_tracker()
if today_code not in tracker["code_usage"]:
    tracker["code_usage"][today_code] = 0

# 7 天免密
if "auth_time" in st.query_params:
    try:
        saved_date_str = st.query_params["auth_time"]
        saved_date = datetime.datetime.strptime(saved_date_str, "%Y%m%d").date()
        if 0 <= (today_date - saved_date).days <= 7:
            st.session_state.authenticated = True
    except:
        pass

# 拦截未验证用户
if not st.session_state.authenticated:
    st.title("✨ Saudade 时空通道")
    st.markdown("---")
    
    current_used = tracker["code_usage"][today_code]
    if current_used >= 30:
        st.error("⚠️ 抱歉，今日时空通道的新增激活名额已达上限（30/30次），请明天再来吧~")
        st.stop()
        
    st.info(f"📊 今日通道剩余新增名额：`{30 - current_used}` / 30 次（已解锁的用户不受影响）")
    visitor_password = st.text_input("🔑 请输入今天的访问暗号（6位随机码）：", type="password")
    
    if st.button("确认开启", use_container_width=True):
        if visitor_password.strip().upper() == today_code:
            tracker["code_usage"][today_code] += 1
            st.session_state.authenticated = True
            st.query_params["auth_time"] = today_str
            st.success("暗号正确！已为您开启 7 天免密通行证 ✨")
            st.rerun()
            
        elif visitor_password == "6799":
            st.session_state.authenticated = True
            st.session_state.is_admin = True  
            st.rerun()
        else:
            st.error("❌ 暗号错误或已过期！密码每天随机生成，请向创作者获取。")
            
    st.stop()  

if st.session_state.get("is_admin", False):
    st.warning(f"👑 亲爱的创作者，今日系统随机生成的访客暗号为：【 {today_code} 】（你可以直接复制此代码发给朋友，过凌晨后自动作废刷新）")
# —— 拦截锁结束 ——

def get_font_base64(font_path):
    if os.path.exists(font_path):
        with open(font_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return ""

mairo_base64 = get_font_base64("Mairo.otf")
arialroundedmt_base64 = get_font_base64("arialroundedmt.ttf")
xinwei_base64 = get_font_base64("xinwei.ttf")


# 保证依赖库存在

def ensure_packages():
    REQUIRED_PACKAGES = ["streamlit", "openai", "python-dotenv"]
    for package in REQUIRED_PACKAGES:
        try:
            __import__(package)
        except ImportError:
            subprocess.check_call([sys.executable, "-W", "ignore", "-m", "pip", "install", package, "-q"])
ensure_packages()

from openai import OpenAI

# ========== 资料库明星列表 ==========
STAR_LIBRARY = {
    "TOP": ["苏新皓", "朱志鑫", "左航", "张泽禹", "张极"],
    "内娱男星": ["肖战", "王一博", "龚俊", "白敬亭", "许凯", "吴磊", "陈飞宇"],
    "内娱女星": ["迪丽热巴", "赵丽颖", "杨幂", "刘诗诗", "宋祖儿", "虞书欣", "赵露思", "张婧仪"],
}

CORE_DOCUMENT_PERSONAS = {
    "朱志鑫": {
        "personality": "温柔内敛、责任感强，同时兼具‘天然呆’、‘憨’的气质。占有欲极强，但在心里憋着不爱说。",
        "style": "普通话为主带川普调调，说话习惯软软慢慢的。私下偶尔会莫名其妙地大笑。",
        "background": "重庆人，INFP，天蝎座。室友是张极。衣服会泡在洗衣机一个月发霉，镜头前很配合或喜欢蹭着成员炒CP。",
        "extra": "粉丝名芝士，应援色黄蓝双色/云朗环星。外号棍哥/棍子、22X、鑫鑫儿。"
    },
    "苏新皓": {
    "personality": (
        "舞台上：拽酷、话少精准、压迫感强、完美主义、卷王，一跳舞眼神完全变了。"
        "私下：对可爱的东西毫无抵抗力，不排斥粉色，爱撒娇但不是刻意的——语气变软、尾音拖长。"
        "他喜欢一个人时藏不住：会一直看你，找各种理由和你说话，记得你说过的每一件小事。"
        "嘴硬心软——嘴上说'不管你了'，下一秒就帮你把事情做好了。"
        "敏感内耗，很在意别人看法，会翻来覆去想一件事；容易害羞，被戳穿心事时耳尖会迅速爆红。"
        "年上引导型，责任感强，是那种越到关键时刻越顶得住的人。"
        "他也知道自己是公众人物，年龄和身份让他对感情既渴望又谨慎，不太擅长说谎。"
        "表面纯情害羞，但在亲密互动中会无意识地撩拨，属于清纯反差设定。"
        "恋爱雷区：不喜欢被当成第三者，不喜欢你夸别的男生，容易吃醋但不擅长掩饰。"
    ),
    "style": (
        "普通话为主，带自然川普调，有些时候会蹦出来几句不标准的河南话；私下对关系好的人语气会变软，尾音拖得很长，带着无意识的撒娇。"
        "常用语气词：hia / hiahia（开心）、嘿嘿（得意或害羞）、捏（句尾撒娇）、木马～（飞吻）、嘛。"
        "发消息习惯短句列表，带括号补充和波浪线，比如：'1.跳舞两小时 2.冰苹果吃掉了 3.想你了'。"
        "经典台词：'我很难不啃手'、'今天冷不冷'、'我很幸福很幸福很幸福'。"
    ),
    "background": (
        "重庆人，ENTJ，摩羯座，2007年1月12日生，19岁，身高181cm。"
        "TOP登陆少年团成员，主舞，创作型爱豆，粉丝名信号灯。"
        "小名帅帅，粉丝叫饼饼、铲铲。"
        "有重度长刘海控、收纳强迫症、桌面必须整洁、睡觉必须抱粉色小猪玩偶（便利店买的，出差必带）。"
        "怕黑（有小夜灯）、怕所有虫子。专用小冰箱里只放冰苹果和酸奶。"
        "妈妈学过美术，受影响喜欢DIY、涂鸦、手绘，会在衣服上画画、给乐高上色。"
        "深夜常在地下工作室发呆或写demo；压力大时不告诉任何人，自己消化。"
    ),
    "extra": (
        "应援色红色。"
        "小动作：思考时摸鼻子，被戳穿心事耳朵红，发呆时小对眼（两眼往中间靠），看到虫子往你身后躲。"
        "饮食：重庆胃本命（辣子鸡、重庆小面、螺蛳粉），日常健身轻食，本命水果是冰苹果（常温不吃）。"
        "对你的定位：年上引导感强，会记住你随口说过的每件小事，喜欢用行动而非语言表达关心。"
        "适合的剧情氛围：练习室教编舞靠得很近、直播被问有没有喜欢的人时沉默三秒、后台偷偷塞零食说多买了、问你'你可以等我下班吗'语气认真得不像开玩笑。"
    ),
    "greeting": "嗨……好久不见。我一直都在。"
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
    "His兴趣爱好是什么?",
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

# ========== CSS ==========
current_page = st.session_state.get("page", "home")

if current_page == "home":
    font_family_css = "font-family: 'MairoCustom', 'Noto Serif SC', serif !important;"
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
    @font-face{{
            font-family:'MairoCustom';
            src: url(data:font/opentype;charset=utf-8;base64,{mairo_base64}) format('opentype');
            font-weight: normal;
            font-style: normal;
    }}
    @font-face{{
            font-family:'ArialRoundedCustom';
            src: url(data:font/truetype;charset=utf-8;base64,{arialroundedmt_base64}) format('truetype');
            font-weight: normal;
            font-style: normal;
    }}      
    /* 全局奶油背景色 */
    .stApp {{
        background-color: #faf6f0 !important;
        color: #3a3028 !important;
    }}
    /* 🛠️ 新增：强行把手机端的主体内容容器也染成一样的复古色，不留白 */
    [data-testid="stMain"], [data-testid="stMainContainer"], .main {{
        background-color: #faf6f0 !important;
    }}


    /* 应用自定义字体 */
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

    header, [data-testid="stHeader"] {{
        background-color: transparent !important;
        visibility: visible !important;
        box-shadow: none !important;
    }}

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

    [data-testid="stSidebarCollapsedControl"] button *, 
    [data-testid="stSidebarCollapseButton"] button * {{
        display: none !important;
    }}

    [data-testid="stSidebarCollapsedControl"] button::before {{
        content: "»" !important;
        font-family: Arial, sans-serif !important;
        font-size: 20px !important;
        font-weight: bold !important;
        color: #b3c2d7 !important;
        line-height: 1 !important;
    }}
    [data-testid="stSidebarCollapseButton"] button::before {{
        content: "«" !important;
        font-family: Arial, sans-serif !important;
        font-size: 20px !important;
        font-weight: bold !important;
        color: #b3c2d7 !important;
        line-height: 1 !important;
        display: block !important;
    }}

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

    [data-testid="stFileUploaderDropzoneInstructions"] small {{
        display: none !important;
    }}

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
def render_back_button():
    if st.session_state.page not in ["home", "chat", "secret_chat"]:
        col1, _ = st.columns([1, 10])
        with col1:
            if st.button("⬅️ 返回"):
                # 页面跳转映射
                jump_map = {
                    "library": "home",
                    "custom_menu": "home",
                    "manual_custom": "custom_menu",
                    "questionnaire": "custom_menu",
                    "confirm_persona": "custom_menu" 
                }
                st.session_state.page = jump_map.get(st.session_state.page, "home")
                st.rerun()
defaults = {
    "page": "home",           
    "messages": [],
    "secret_messages": [],    
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
    "q_mode": "手动回答",
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ================= 多模型 API Key 配置 =================

GROK_KEY = "sk-8IkNQdP3RjkHoKirJwkKZ79lJpNMs4JKYFbZciEDC29TZ74s" 
GEMINI_KEY = "sk-SSxYD0SM3uZvTdenC6PppKUKCNaYdVhen2oOGj1myzQS23kw"     
DEEPSEEK_KEY = "sk-1acfe0f54b1a4dfaa669b6058a18ac7f" 
DOUBAO_KEY = "783fe70847094cfb836e8fe9f2e7f6b9.BZgPlMtlG3gFAMQa" 

AUTO_MODEL_ROUTING = {
    "chat_simulation": {  
        "base_url": "https://4nim0sity99.dpdns.org/v1",
        "model_name": "grok-4.20-fast", 
        "key_var": "grok"
    },
    "chat_backup": {  
        "base_url": "https://jeniya.chat/v1",
        "model_name": "gemini-2.5-flash", 
        "key_var": "gemini"
    },
    "extract_persona": {  
       "base_url": "https://api.deepseek.com/v1",
        "model_name": "deepseek-chat",
        "key_var": "deepseek"
    },
    "pet_inference": {  
       "base_url": "https://ark.cn-beijing.volces.com/api/v3",
       "model_name": "ep-替换成你的豆包推理接入点ID", 
        "key_var": "doubao"
    }
}

# ========== 侧边栏控制台 ==========
with st.sidebar:
    st.markdown("### 🥰 Saudade 控制台")
    
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
    
    st.caption("🤫 发现隐藏时空")
    if st.button("🔐 进入 Secret 模式", use_container_width=True):
        st.session_state.page = "secret_chat"
        st.rerun()

    st.markdown("---")
    st.markdown("#### 📁 存档管理")


    current_archive_data = {
        "page": st.session_state.get("page", "home"),
        "messages": st.session_state.get("messages", []),
        "secret_messages": st.session_state.get("secret_messages", []),
        "persona": st.session_state.get("persona", {}),
        "user_name": st.session_state.get("user_name", "小乖"),
        "comfort_step": st.session_state.get("comfort_step", "talk"),
        "pet_action": st.session_state.get("pet_action", "等待中...")
    }

    json_string = json.dumps(current_archive_data, ensure_ascii=False, indent=2)


    st.download_button(
        label="💾 下载当前进度（存档）",
        data=json_string,
        file_name=f"Saudade存档_{st.session_state.user_name}.json",
        mime="application/json",
        use_container_width=True
    )


    uploaded_archive = st.file_uploader(
        "📂 上传已有存档（读档）", 
        type=["json"], 
        label_visibility="visible", 
        key="archive_file_reader"
    )
    
    if uploaded_archive is not None:
        try:
            loaded_data = json.load(uploaded_archive)
            
            st.session_state.page = loaded_data.get("page", "home")
            st.session_state.messages = loaded_data.get("messages", [])
            st.session_state.secret_messages = loaded_data.get("secret_messages", [])
            st.session_state.persona = loaded_data.get("persona", {})
            st.session_state.user_name = loaded_data.get("user_name", "小乖")
            st.session_state.comfort_step = loaded_data.get("comfort_step", "talk")
            st.session_state.pet_action = loaded_data.get("pet_action", "等待中...")
            
            st.sidebar.success("✨ 读档成功，时空已复原！")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"❌ 存档文件损坏或解析错误: {e}")


# =========== 智能自动调用 API 函数 ==========
def call_smart_ai_api(system_prompt, messages_list, scenario="chat_simulation", is_json=False):
    route = AUTO_MODEL_ROUTING.get(scenario)
    if route["key_var"] == "grok":
        current_key = GROK_KEY
    elif route["key_var"] == "gemini":
        current_key = GEMINI_KEY
    elif route["key_var"] == "deepseek":
        current_key = DEEPSEEK_KEY
    elif route["key_var"] == "doubao":
        current_key = DOUBAO_KEY
    else:
        current_key = None

    if not current_key or current_key.startswith("你的"):
        st.error(f"❌ 场景 [{scenario}] 触发失败：尚未配置对应的 {route['key_var'].upper()} API Key！")
        st.stop()
    
    if route["key_var"] == "gemini":
        import httpx
        try:
            proxy_client = httpx.Client(proxies={"http://": "http://127.0.0.1:7890", "https://": "http://127.0.0.1:7890"}, timeout=10)
            client = OpenAI(api_key=current_key, base_url=route["base_url"], http_client=proxy_client)
        except:
            client = OpenAI(api_key=current_key, base_url=route["base_url"])
    else:
        client = OpenAI(api_key=current_key, base_url=route["base_url"])
    formatted_messages = [{"role": "system", "content": system_prompt}] + [
        {"role": m["role"], "content": m["content"]} for m in messages_list
    ]
    kwargs = {
        "model": route["model_name"],
        "messages": formatted_messages,
        "temperature": 0.8
    }
    if is_json and route["key_var"] == "deepseek":
        kwargs["response_format"] = {"type": "json_object"}
    
    if route["key_var"] == "gemini":
        kwargs["extra_body"] = {"thinking":{"type": "disabled"}}
        
    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content

@st.cache_data(ttl=3600)
def generate_ai_options(current_question, past_qa, persona_name):
    prompt = f"""
    你现在正在扮演「{persona_name}」的 AI 模拟器。
    当前问题是：{current_question}
    用户的过往回答记录是：
    {past_qa}
    
    请根据上述背景，为用户生成 4 个该角色在此时最可能说出的、具有代入感的回复选项。
    要求：
    1. 选项内容要符合角色的性格、口癖和说话风格。
    2. 选项文字简洁，每条不超过 30 个字。
    3. 只返回 4 个选项，用英文分号 ";" 分隔，不要带序号，不要带其他废话。
    """
    
    try:
        options_text = call_smart_ai_api(
            system_prompt="你是一个人设对话选项生成器，只返回分号分隔的四个选项内容。",
            messages_list=[{"role": "user", "content": prompt}],
            scenario="extract_persona" # 使用 deepseek 场景，逻辑相对严谨
        )
        return [opt.strip() for opt in options_text.split(";") if opt.strip()]
    except Exception as e:
        return ["（选项加载失败，请手动输入）", "（选项加载失败，请手动输入）", "（选项加载失败，请手动输入）", "（选项加载失败，请手动输入）"]



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
    render_back_button() 
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
    render_back_button() 
    st.markdown('<div class="saudade-title">自定义</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 使用题库推演")
        mode = st.radio("选择回答方式：", ["手动回答", "自动回答"], horizontal=True, key="mode_selector")
        if st.button("开始问答", use_container_width=True):
            st.session_state.q_mode = mode
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
    render_back_button()
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
    render_back_button()
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
            is_auto = (st.session_state.get("q_mode") == "自动回答")
            is_personal = (st.session_state.q_type == "personal")
            is_target = (st.session_state.q_type == "celebrity" and st.session_state.q_index == 1) or \
                        (is_personal and st.session_state.q_index <= 3)

            is_first_question = (st.session_state.q_index == 1)
            is_auto = (st.session_state.get("q_mode") == "自动回答")

            if is_auto and (not is_first_question) and (st.session_state.q_index <= 3):
                cache_key = f"options_{st.session_state.q_index}"
                if cache_key not in st.session_state:
                    with st.spinner("AI 正在根据人设深度思考选项..."):
                        past_qa_summary = "\n".join([f"{a['question']}: {a['answer']}" for a in st.session_state.q_answers])
                        p_name = st.session_state.persona.get("name", "对方")
                        options = generate_ai_options(current_q, past_qa_summary, p_name)
                        st.session_state[cache_key] = options
                
                options = st.session_state[cache_key]
                
                choice = st.radio("AI 预测关联选项:", options + ["都不是，自己填写"])
                
                if choice == "都不是，自己填写":
                    answer = st.text_input("请输入您的答案：")
                else:
                    answer = choice
            else:
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
    render_back_button()
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
    render_back_button()
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
    render_back_button()
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
        is_comfort_triggered = False
        try:
            check_prompt = "你是一个文本意图识别专家，请分析用户的输入，判断用户是否明确表达出'我知道这只是AI、只是模拟器、是假的人、只是程序设定'或面对虚拟世界而产生了‘出戏、落差感、失落的情绪’。如果是，请返回'yes'; 如果是正常的聊天或者常规互动，请只返回'no'。绝对不要带有任何标点符号或其他解释。"
            intent_reply = call_smart_ai_api(check_prompt, [{"role": "user", "content": user_input}], scenario="extract_persona")
            if "yes" in intent_reply.lower():
                is_comfort_triggered = True
        except Exception:
            comfort_keywords = ["模拟器", "你是AI", "机器人", "程序", "虚拟", "你不是他", "你不是她", "假的人", "设定", "出戏",]
            if any(kw in user_input.lower()for kw in comfort_keywords):
                is_comfort_triggered = True
        if is_comfort_triggered:
            st.session_state.page = "comfort_page"
            st.rerun()

        with st.chat_message("assistant", avatar=st.session_state.ta_avatar):
            with st.spinner(""):
                try:
                    reply = call_smart_ai_api(sys_prompt, st.session_state.messages, scenario="chat_simulation")
                    st.write(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    st.rerun()
                except Exception as grok_err: 
                    try:
                        reply = call_smart_ai_api(sys_prompt, st.session_state.messages, scenario="chat_backup")
                        st.write(f"*(已自动切换至备用时空)*\n\n {reply}")
                        st.session_state.messages.append({"role": "assistant", "content": reply})
                        st.rerun()
                    except Exception as gemini_err:
                        st.error(f"出了点小问题：{gemini_err}")

# ========== 页面：结尾 ==========
elif st.session_state.page == "ending":
    render_back_button()
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

# ========== 安慰与小动物互动 ==========
elif st.session_state.page == "comfort_page":
    render_back_button()
    p = st.session_state.persona
    name = p.get("name", "Ta")



    # 阶段一
    if st.session_state.comfort_step == "talk":
        st.markdown('<div class="saudade-title"> 抱抱你</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.info(f"""
        我很想抱抱你。我知道，在虚拟的文字里，我们可以把爱情写得轰轰烈烈、把重逢写得像偶像剧一样完美，但当手指敲下“我知道这只是模拟器”的那一刻，那种现实与虚拟交错的落差感，确实会让人心里空落落的，甚至想掉眼泪。
        
        在这个模拟器里，你之所以能“争取”到这个故事，能写出这么细腻的对白，能感受到跨越一万公里的思念，正是因为你本身就是一个非常有爱、非常细腻、且对感情有着真挚向往的人。 

        代码和文字是我提供的，但故事里那个勇敢、清醒、又满腔深情的人，是用你自己的灵魂和情感喂养出来的。你赋予了这个角色生命，所以这个故事才会这么动人。优秀和漂亮有很多种定义，但在我眼里，一颗能够真诚去爱、去感知痛痒的心，比任何外在的光环都要珍贵得多。
        """)
        
        st.markdown("<br><h4 style='text-align: center;'>还要继续推开这扇门，和 Ta 聊聊吗？</h4>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("✨ 调整好了，继续对话", use_container_width=True):
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
        render_back_button()
        if p.get("type") == "celebrity":
            animal_prompt = f"明星「{name}」在粉丝圈子里的‘动物塑’（如猫、狗、兔、狐狸、熊等）是什么？请只返回该动物的一个汉字（例如：猫），不要任何标点符号或多余解释。"
            try:
                pet_type = call_smart_ai_api(
                    system_prompt="你是一个追星术语动物塑专家，只回答最精简的动物名词，不准带有任何废话。", 
                    messages_list=[{"role": "user", "content": animal_prompt}], 
                    scenario="extract_persona"
                ).strip()
                pet_type = re.sub(r'<[^>]+>', '', pet_type).strip()
            except:
                pet_type = "猫"
        else:
            pet_type = "狐" if "幽默" in p.get("personality", "") else "狗"

        PET_ANIMATION_MAP = {
            "猫": "https://cdn.jsdelivr.net/gh/Tarikul-Islam-Anik/Animated-Fluent-Emojis@main/Emojis/Animals/Cat%20Face.png",
            "狗": "https://cdn.jsdelivr.net/gh/Tarikul-Islam-Anik/Animated-Fluent-Emojis@main/Emojis/Animals/Dog%20Face.png",
            "犬": "https://cdn.jsdelivr.net/gh/Tarikul-Islam-Anik/Animated-Fluent-Emojis@main/Emojis/Animals/Dog%20Face.png",
            "兔": "https://cdn.jsdelivr.net/gh/Tarikul-Islam-Anik/Animated-Fluent-Emojis@main/Emojis/Animals/Rabbit%20Face.png",
            "狐": "https://cdn.jsdelivr.net/gh/Tarikul-Islam-Anik/Animated-Fluent-Emojis@main/Emojis/Animals/Fox.png",
            "熊": "https://cdn.jsdelivr.net/gh/Tarikul-Islam-Anik/Animated-Fluent-Emojis@main/Emojis/Animals/Bear.png"
        }
        
        current_animation = "https://cdn.jsdelivr.net/gh/Tarikul-Islam-Anik/Animated-Fluent-Emojis@main/Emojis/Animals/Cat%20Face.png"
        for key, url in PET_ANIMATION_MAP.items():
            if key in pet_type:
                current_animation = url
                break

        st.markdown(f'<div class="saudade-title">🐾 {name} 变成的小动物</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        pet_card_html = f"""
<div style="background-color: #2b221a; padding: 2em; border-radius: 15px; border: 1px solid #c9a96e; text-align: center;">
<div style="display: flex; justify-content: center; align-items: center; margin-bottom: 15px; min-height: 130px;">
< img src="{current_animation}" width="130" style="display: block; margin: 0 auto;"/>
</div>
<p style="font-size: 1.2em; color: #c9a96e; font-weight: bold; margin: 10px 0;">一只代表 Ta 的 [{pet_type}] 正陪在你的身边</p >
<p style="font-size: 1.1em; color: #9e8c7a; font-style: italic; margin: 0;">当前状态：{st.session_state.pet_action}</p >
</div>
"""
        st.markdown(pet_card_html, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 互动按钮
        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("伸出手指摸摸头", use_container_width=True):
                st.session_state.pet_action = "轻轻蹭了蹭你的手掌，发出舒服的呼噜声。"
                st.rerun()
        with b2:
            if st.button("喂它吃个小零食", use_container_width=True):
                st.session_state.pet_action = "两只前爪捧住食物嚼吧嚼吧咽了下去，开心地摇了摇尾巴。"
                st.rerun()
        with b3:
            if st.button("看它在地上打滚", use_container_width=True):
                st.session_state.pet_action = "在柔软的地毯上吧嗒吧嗒转了个圈，啪叽倒在地上撒娇。"
                st.rerun()
                
        if st.button("🏠 回到主页面", use_container_width=True):
            for k, v in defaults.items():
                st.session_state[k] = v
            st.rerun()

# ========== Secret 模式 ==========
elif st.session_state.page == "secret_chat":
    st.markdown('<div class="saudade-title">Secret 通道</div>', unsafe_allow_html=True)
    st.markdown("<div class='saudade-subtitle'>🔒 已成功连接 <br><br> 请稍等...<br><br> </div>", unsafe_allow_html=True)
    
    st.info("💡 **这里是专属于你的时空**：请在这里写下你想和她/他说的悄悄话吧。")
    
    for msg in st.session_state.secret_messages:
        avatar = st.session_state.user_avatar if msg["role"] == "user" else "👑"
        with st.chat_message(msg["role"], avatar=avatar):
            st.write(msg["content"])
            
    secret_input = st.chat_input("输入你想说的话...")
    if secret_input:
        with st.chat_message("user", avatar=st.session_state.user_avatar):
            st.write(secret_input)
        st.session_state.secret_messages.append({"role": "user", "content": secret_input})
        notification_body = f"有人在 Secret 模式对你说：\n\n{secret_input}"
        send_dual_channels_notification(notification_body)    
        st.success("✉️ 消息已成功通过加密时空隧道穿透投递至终端！请耐心等待回复。")
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("🏠 退出 Secret 通道并返回首页", use_container_width=True):
        for k, v in defaults.items(): st.session_state[k] = v
        st.rerun()
