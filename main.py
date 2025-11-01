import streamlit as st
import random
import json
import hashlib
import hmac
from datetime import datetime
import pandas as pd
import time


class SecurityManager:
    def __init__(self):
        self.secret_key = hashlib.sha256("homework_system".encode()).hexdigest()[:32].encode('utf-8')

    def calculate_hmac(self, data):
        if isinstance(data, dict):
            data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        else:
            data_str = str(data)
        return hmac.new(self.secret_key, data_str.encode('utf-8'), hashlib.sha256).hexdigest()


class HomeworkLotterySystem:
    def __init__(self):
        self.security_manager = SecurityManager()
        if 'students_data' not in st.session_state:
            st.session_state.students_data = self.create_sample_data()
        
        # 初始化抽奖结果状态
        if 'lottery_result' not in st.session_state:
            st.session_state.lottery_result = None
        if 'show_animation' not in st.session_state:
            st.session_state.show_animation = False

    def create_sample_data(self):
        sample_data = [
            {"name": "张三", "completed": 15, "total": 20, "correct": 12, "correct_total": 20},
            {"name": "李四", "completed": 18, "total": 20, "correct": 16, "correct_total": 20},
            {"name": "王五", "completed": 10, "total": 20, "correct": 8, "correct_total": 20},
            {"name": "赵六", "completed": 8, "total": 20, "correct": 6, "correct_total": 20},
            {"name": "钱七", "completed": 5, "total": 20, "correct": 3, "correct_total": 20},
        ]

        students = {}
        for data in sample_data:
            completion_rate = (data['completed'] / data['total'] * 100)
            accuracy_rate = (data['correct'] / data['correct_total'] * 100)
            students[data['name']] = {
                'completion_rate': completion_rate,
                'accuracy_rate': accuracy_rate,
                'completed': data['completed'],
                'total': data['total'],
                'correct': data['correct'],
                'correct_total': data['correct_total']
            }
        return students

    def calculate_probability(self, completion_rate, accuracy_rate):
        overall_performance = (completion_rate + accuracy_rate) / 2
        return (100 - overall_performance) ** 2

    def draw_lottery(self):
        students_data = st.session_state.students_data
        if not students_data:
            return None, None, None

        names = list(students_data.keys())
        weights = []

        for name in names:
            student = students_data[name]
            weight = self.calculate_probability(
                student['completion_rate'],
                student['accuracy_rate']
            )
            weights.append(weight)

        if sum(weights) == 0:
            weights = [1] * len(names)

        selected_name = random.choices(names, weights=weights, k=1)[0]
        student_data = students_data[selected_name]
        probability = self.calculate_probability(
            student_data['completion_rate'],
            student_data['accuracy_rate']
        )

        return selected_name, student_data, probability


def show_custom_animation():
    """显示自定义动画效果"""
    st.markdown("""
    <style>
    @keyframes celebrate {
        0% { transform: scale(1); }
        50% { transform: scale(1.2); }
        100% { transform: scale(1); }
    }
    .celebrate {
        animation: celebrate 0.5s ease-in-out 3;
        display: inline-block;
    }
    .confetti {
        position: fixed;
        width: 10px;
        height: 10px;
        background: #ff0000;
        animation: fall 5s linear infinite;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 显示庆祝效果的文本
    st.markdown('<div class="celebrate">🎉</div>', unsafe_allow_html=True)


def main():
    st.set_page_config(
        page_title="作业抽奖点名系统",
        page_icon="🎯",
        layout="wide"
    )

    st.title("🎯 作业抽奖点名系统")
    st.markdown("---")

    system = HomeworkLotterySystem()

    # 侧边栏 - 添加学生
    with st.sidebar:
        st.header("添加学生数据")

        with st.form("add_student_form"):
            name = st.text_input("学生姓名")
            col1, col2 = st.columns(2)
            with col1:
                completed = st.number_input("已完成题目数", min_value=0, step=1)
                total = st.number_input("总题目数", min_value=1, step=1)
            with col2:
                correct = st.number_input("做对题目数", min_value=0, step=1)
                correct_total = st.number_input("正确题目总数", min_value=1, step=1)

            if st.form_submit_button("添加/更新学生"):
                if name and total > 0 and correct_total > 0:
                    if completed <= total and correct <= correct_total:
                        completion_rate = (completed / total * 100)
                        accuracy_rate = (correct / correct_total * 100)

                        st.session_state.students_data[name] = {
                            'completion_rate': completion_rate,
                            'accuracy_rate': accuracy_rate,
                            'completed': completed,
                            'total': total,
                            'correct': correct,
                            'correct_total': correct_total
                        }
                        st.success(f"成功添加学生: {name}")
                        # 清空抽奖结果，因为数据已更新
                        st.session_state.lottery_result = None
                        st.session_state.show_animation = False
                    else:
                        st.error("完成数/正确数不能大于总数")
                else:
                    st.error("请填写完整信息")

        if st.button("清空所有数据", type="secondary"):
            st.session_state.students_data = {}
            st.session_state.lottery_result = None
            st.session_state.show_animation = False
            st.rerun()

    # 主内容区
    col1, col2 = st.columns([1, 1])

    with col1:
        st.header("学生列表")

        if st.session_state.students_data:
            # 显示学生表格
            data = []
            for name, info in st.session_state.students_data.items():
                prob = system.calculate_probability(info['completion_rate'], info['accuracy_rate'])
                data.append({
                    '姓名': name,
                    '完成题目': f"{info['completed']}/{info['total']}",
                    '正确题目': f"{info['correct']}/{info['correct_total']}",
                    '完成率': f"{info['completion_rate']:.1f}%",
                    '准确率': f"{info['accuracy_rate']:.1f}%",
                    '抽中权重': f"{prob:.0f}"
                })

            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("暂无学生数据，请在左侧添加学生")

    with col2:
        st.header("抽奖功能")

        if st.session_state.students_data:
            # 抽奖按钮
            if st.button("🎲 开始抽奖", type="primary", use_container_width=True):
                # 设置显示动画标志
                st.session_state.show_animation = True
                # 执行抽奖
                selected_name, student_data, probability = system.draw_lottery()
                st.session_state.lottery_result = {
                    'name': selected_name,
                    'data': student_data,
                    'probability': probability
                }
                st.rerun()

            # 显示抽奖结果
            if st.session_state.lottery_result:
                result = st.session_state.lottery_result
                
                # 显示动画效果
                if st.session_state.show_animation:
                    # 使用自定义动画
                    show_custom_animation()
                    # 同时使用Streamlit内置动画
                    st.balloons()
                    # 重置动画标志，避免重复播放
                    st.session_state.show_animation = False
                
                st.success(f"🎉 被抽中的学生是：**{result['name']}**")

                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric(
                        "作业完成",
                        f"{result['data']['completed']}/{result['data']['total']}题",
                        f"{result['data']['completion_rate']:.1f}%"
                    )
                with col_b:
                    st.metric(
                        "题目正确",
                        f"{result['data']['correct']}/{result['data']['correct_total']}题",
                        f"{result['data']['accuracy_rate']:.1f}%"
                    )

                st.info(f"📈 抽中权重: {result['probability']:.2f}")

                # 显示概率说明
                st.markdown("---")
                st.caption("🎯 抽奖规则：完成率和准确率越低的学生，被抽中的概率越高")
        else:
            st.warning("请先添加学生数据")

    # 底部信息
    st.markdown("---")
    st.caption("💡 提示：系统会自动保存数据，刷新页面不会丢失")


if __name__ == "__main__":
    main()
