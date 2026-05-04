"""配置加载模块"""
import yaml
import json
import os


class ConfigLoader:
    """配置加载器"""

    @staticmethod
    def load_config(config_path: str = 'config/production.yaml') -> dict:
        """加载YAML配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                print(f"Loaded config from {config_path}")
                return config
        except FileNotFoundError:
            print(f"Config file not found: {config_path}")
            # 返回默认配置
            return ConfigLoader._default_config()
        except Exception as e:
            print(f"Error loading config: {e}")
            return ConfigLoader._default_config()

    @staticmethod
    def load_companies(companies_path: str = 'config/companies.json') -> list:
        """加载公司配置JSON（包含P0、P1、P2和P3公司）"""
        try:
            with open(companies_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

                # 加载 P0 公司
                p0_companies = data.get('p0_companies', [])

                # 加载 P1 公司
                p1_companies = data.get('p1_companies', [])

                # 加载 P2 公司（全加拿大工签友好）
                p2_companies = data.get('p2_companies', [])

                # 加载 P3 公司（大银行等企业）
                p3_companies = data.get('p3_companies', [])

                # 合并所有列表
                all_companies = p0_companies + p1_companies + p2_companies + p3_companies

                print(f"Loaded {len(p0_companies)} P0 + {len(p1_companies)} P1 + {len(p2_companies)} P2 + {len(p3_companies)} P3 companies = {len(all_companies)} total")
                return all_companies
        except Exception as e:
            print(f"Error loading companies: {e}")
            return []

    @staticmethod
    def _default_config() -> dict:
        """默认配置"""
        return {
            'debug': {
                'enabled': False  # 默认关闭调试
            },
            'schedule': {
                'hours': [8, 12, 18]
            },
            'storage': {
                'vault_dir': '/Users/xxm/projects/QuantEngine_markdown_file/12-找工作'
            },
            'location_filter': [
                'Calgary, Alberta',
                'Edmonton, Alberta',
                'Alberta, Canada',
                'Canada, Remote',
                'Toronto, Ontario',
                'Vancouver, British Columbia',
                'Unknown'  # 临时：允许未知地点
            ],
            'tech_keywords': [
                'Software', 'Development', 'Director', 'Manager', 'Lead',
                'DevOps', 'Engineer', 'Staff', 'Senior', 'Owner'
            ],
            'level_keywords': [
                'Director', 'Manager', 'Senior', 'Staff', 'Lead'
            ],
            'exclude_keywords': [
                'contract', 'contractor', 'hourly',
                'internship', 'junior', 'intern',
                'student', 'coordinator'
            ],
            'request': {
                'timeout': 10,
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        }
