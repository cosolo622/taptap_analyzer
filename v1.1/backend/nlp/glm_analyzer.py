# -*- coding: utf-8 -*-
"""
阿里百炼Coding Plan API 分析器
支持模型: glm-5, qwen3.5-plus, kimi-k2.5 等
"""
import os
import json
import re
from datetime import datetime
from typing import Dict, Optional
import requests

# Token配置
DAILY_TOKEN_LIMIT = 100000  # 每日Token限额
PER_REQUEST_TOKEN_LIMIT = 500  # 单次请求Token限额

# 阿里百炼配置
ALIYUN_API_KEY = os.environ.get('ALIYUN_API_KEY', 'sk-sp-873fa25290a343ce9493e2d260bf887b')
ALIYUN_BASE_URL = "https://coding.dashscope.aliyuncs.com/v1"
DEFAULT_MODEL = "glm-5"  # 可选: qwen3.5-plus, glm-5, kimi-k2.5


class TokenTracker:
    """Token消耗追踪器"""
    
    def __init__(self, log_file: str = None):
        if log_file is None:
            log_file = os.path.join(os.path.dirname(__file__), '..', 'logs', 'token_usage.json')
        
        self.log_file = log_file
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        self.total_tokens = 0
        self.daily_tokens = 0
        self.today = datetime.now().strftime('%Y-%m-%d')
        
        self._load_today_usage()
    
    def _load_today_usage(self):
        """加载今日Token使用量"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for entry in data:
                    if entry.get('timestamp', '').startswith(self.today):
                        self.daily_tokens += entry.get('total', 0)
                
                self.total_tokens = sum(e.get('total', 0) for e in data)
            except:
                pass
    
    def log_usage(self, prompt_tokens: int, completion_tokens: int, model: str, review_id: str = None) -> Dict:
        """记录一次API调用的token消耗"""
        total = prompt_tokens + completion_tokens
        self.total_tokens += total
        self.daily_tokens += total
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'date': self.today,
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens,
            'total': total,
            'model': model,
            'review_id': review_id,
            'daily_total': self.daily_tokens
        }
        
        self._append_log(entry)
        return entry
    
    def _append_log(self, entry: Dict):
        """追加日志"""
        logs = []
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            except:
                logs = []
        
        logs.append(entry)
        logs = logs[-10000:]
        
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    
    def can_request(self, estimated_tokens: int) -> tuple:
        """检查是否可以发起请求"""
        if self.daily_tokens >= DAILY_TOKEN_LIMIT:
            return False, f"今日Token额度已用完: {self.daily_tokens}/{DAILY_TOKEN_LIMIT}"
        if estimated_tokens > PER_REQUEST_TOKEN_LIMIT:
            return False, f"单次请求超过限制: {estimated_tokens} > {PER_REQUEST_TOKEN_LIMIT}"
        return True, None
    
    def get_daily_report(self) -> Dict:
        """获取每日报告"""
        return {
            'date': self.today,
            'daily_tokens': self.daily_tokens,
            'daily_limit': DAILY_TOKEN_LIMIT,
            'remaining': DAILY_TOKEN_LIMIT - self.daily_tokens,
            'usage_rate': f"{self.daily_tokens / DAILY_TOKEN_LIMIT * 100:.1f}%"
        }


class AliyunAnalyzer:
    """阿里百炼API分析器 - 支持多种模型"""
    
    SYSTEM_PROMPT = """你是一个专业的游戏评价分析师。你的任务是分析TapTap游戏评价。

## 输出要求
严格按照以下JSON格式输出，不要输出其他内容：
{
    "sentiment": "正向/负向/中性",
    "problem_category": "大类-细分问题",
    "summary": "20-30字关键信息总结"
}

## 分类体系
- 环境问题：低素质玩家、新手水平差、场外、广告、村规
- 技术问题：闪退、服务器崩溃、掉线、无法进入游戏、音频问题、Bug、发热问题
- 商业化问题：界面设计、充值弹窗、皮肤系统、皮肤定价
- 平衡性问题：任务节奏、阵营平衡、角色平衡、攻击范围
- 内容问题：角色数量、模式数量、玩法单调、角色缺失
- 匹配问题：组队匹配、匹配速度
- 功能问题：屏蔽词、新手引导、界面显示、权限问题
- 运营问题：行为分、奖励发放、账号问题、账号互通
- 功能建议：排位系统、手柄支持、家园系统、单机模式
- 无问题：如果评价没有问题，填写"无问题"

## 情感判断标准
- 正向：表达满意、喜欢、推荐
- 负向：表达不满、批评、抱怨
- 中性：客观陈述，无明显情感倾向

## 注意事项
1. summary必须20-30字，保留关键信息
2. problem_category必须从分类体系中选择
3. 只输出JSON，不要输出其他内容"""
    
    def __init__(self, api_key: str = None, token_tracker: TokenTracker = None, model: str = None):
        """
        初始化分析器
        
        Args:
            api_key: 阿里百炼API密钥
            token_tracker: Token追踪器
            model: 使用的模型 (glm-5, qwen3.5-plus, kimi-k2.5等)
        """
        self.api_key = api_key or ALIYUN_API_KEY
        self.token_tracker = token_tracker or TokenTracker()
        self.model = model or DEFAULT_MODEL
        self.base_url = ALIYUN_BASE_URL
    
    def analyze(self, content: str, review_id: str = None) -> Dict:
        """
        分析单条评价
        
        Args:
            content: 评价内容
            review_id: 评价ID（用于日志）
            
        Returns:
            分析结果: {sentiment, problem_category, summary, success}
        """
        # 截断过长内容
        if len(content) > 500:
            content = content[:500]
        
        # 预估token数（中文约1.5字符/token）
        estimated_tokens = int(len(content) * 0.7 + 200)
        
        # 检查是否可以请求
        can_req, error = self.token_tracker.can_request(estimated_tokens)
        if not can_req:
            return self._get_default_result(error)
        
        try:
            request_headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            request_body = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": f"分析评价：{content}"}
                ],
                "temperature": 0.3,
                "max_tokens": 100
            }
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=request_headers,
                json=request_body,
                timeout=45
            )
            if response.status_code != 200 and ('SSL' in response.text or 'HTTPSConnectionPool' in response.text):
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=request_headers,
                    json=request_body,
                    timeout=45,
                    verify=False
                )
            
            if response.status_code != 200:
                return self._get_default_result(f"API错误: {response.status_code}")
            
            data = response.json()
            
            # 记录token使用
            usage = data.get('usage', {})
            self.token_tracker.log_usage(
                prompt_tokens=usage.get('prompt_tokens', 0),
                completion_tokens=usage.get('completion_tokens', 0),
                model=self.model,
                review_id=review_id
            )
            
            # 解析结果
            result_text = data['choices'][0]['message']['content']
            return self._parse_result(result_text)
            
        except Exception as e:
            if 'HTTPSConnectionPool' in str(e) or 'SSL' in str(e):
                try:
                    response = requests.post(
                        f"{self.base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": self.model,
                            "messages": [
                                {"role": "system", "content": self.SYSTEM_PROMPT},
                                {"role": "user", "content": f"分析评价：{content}"}
                            ],
                            "temperature": 0.3,
                            "max_tokens": 100
                        },
                        timeout=45,
                        verify=False
                    )
                    if response.status_code == 200:
                        data = response.json()
                        usage = data.get('usage', {})
                        self.token_tracker.log_usage(
                            prompt_tokens=usage.get('prompt_tokens', 0),
                            completion_tokens=usage.get('completion_tokens', 0),
                            model=self.model,
                            review_id=review_id
                        )
                        result_text = data['choices'][0]['message']['content']
                        return self._parse_result(result_text)
                except Exception:
                    pass
            return self._get_default_result(f"API调用失败: {str(e)[:50]}")
    
    def _parse_result(self, result_text: str) -> Dict:
        """解析API返回结果"""
        try:
            # 尝试提取JSON
            json_match = re.search(r'\{[^}]+\}', result_text)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(result_text)
            
            # 校验结果
            sentiment = data.get('sentiment', '中性')
            if sentiment not in ['正向', '负向', '中性']:
                sentiment = '中性'
            
            problem_category = data.get('problem_category', '无问题')
            summary = data.get('summary', '分析结果解析失败')
            
            # 校验summary长度
            if len(summary) < 20:
                summary = summary + '，' + '需要更多信息' * ((20 - len(summary)) // 6 + 1)
                summary = summary[:30]
            elif len(summary) > 30:
                summary = summary[:30]
            
            return {
                'sentiment': sentiment,
                'problem_category': problem_category,
                'summary': summary[:30],
                'success': True
            }
        except Exception as e:
            return self._get_default_result(f"解析失败")
    
    def _get_default_result(self, reason: str = "") -> Dict:
        """获取默认结果"""
        return {
            'sentiment': '中性',
            'problem_category': '无问题',
            'summary': f'分析失败: {reason[:20]}'[:30],
            'success': False,
            'reason': reason
        }
    
    def batch_analyze(self, contents: list, max_count: int = None) -> list:
        """批量分析评价"""
        results = []
        count = min(len(contents), max_count or len(contents))
        
        for i, content in enumerate(contents[:count]):
            print(f"  分析中 {i+1}/{count}...")
            result = self.analyze(content)
            results.append(result)
            
            if self.token_tracker.daily_tokens >= DAILY_TOKEN_LIMIT:
                print(f"  今日Token额度已用完，停止分析")
                break
        
        return results


def estimate_token_cost(review_count: int, avg_content_length: int = 100) -> Dict:
    """
    预估Token消耗
    
    Args:
        review_count: 评价数量
        avg_content_length: 平均内容长度
        
    Returns:
        预估结果
    """
    prompt_tokens_per_review = int(avg_content_length * 0.7) + 200
    completion_tokens_per_review = 50
    
    total_per_review = prompt_tokens_per_review + completion_tokens_per_review
    total_tokens = total_per_review * review_count
    
    # 阿里百炼Coding Plan价格（根据实际套餐）
    price_per_1k_tokens = 0.001
    
    estimated_cost = total_tokens * price_per_1k_tokens / 1000
    
    return {
        'review_count': review_count,
        'tokens_per_review': total_per_review,
        'total_tokens': total_tokens,
        'estimated_cost_yuan': round(estimated_cost, 4),
        'daily_limit_reviews': DAILY_TOKEN_LIMIT // total_per_review
    }


def test_analyzer():
    """测试分析器"""
    print("="*50)
    print("测试阿里百炼API分析器")
    print("="*50)
    
    analyzer = AliyunAnalyzer()
    
    # 测试评价
    test_reviews = [
        "游戏很好玩，但是服务器经常崩溃，希望能修复",
        "玩家素质太差了，动不动就骂人，体验很差",
        "还行吧，一般般，没什么特别的"
    ]
    
    for i, review in enumerate(test_reviews):
        print(f"\n测试 {i+1}: {review[:30]}...")
        result = analyzer.analyze(review)
        print(f"  情感: {result['sentiment']}")
        print(f"  分类: {result['problem_category']}")
        print(f"  总结: {result['summary']}")
        print(f"  成功: {result['success']}")
    
    # 打印Token报告
    report = analyzer.token_tracker.get_daily_report()
    print(f"\n今日Token消耗: {report['daily_tokens']}")
    print(f"使用率: {report['usage_rate']}")


if __name__ == '__main__':
    # Token预估
    print("="*50)
    print("Token消耗预估 (阿里百炼Coding Plan)")
    print("="*50)
    
    for count in [3, 5, 10, 50, 100]:
        estimate = estimate_token_cost(count)
        print(f"\n{count}条评价:")
        print(f"  预估Token: {estimate['total_tokens']}")
        print(f"  预估费用: ¥{estimate['estimated_cost_yuan']}")
    
    print(f"\n每日限额: {DAILY_TOKEN_LIMIT} tokens")
    estimate = estimate_token_cost(1)
    print(f"预计每天可分析: {estimate['daily_limit_reviews']} 条评价")
    
    # 运行测试
    print("\n" + "="*50)
    print("运行API测试...")
    print("="*50)
    test_analyzer()
