from freelance.models.project import FreelanceProject
from freelance.utils.logger import get_logger

logger = get_logger(__name__)


class ComplianceFilter:
    def check(self, project: FreelanceProject) -> dict:
        flags = []
        company_signable = True
        text = (project.title + " " + project.description[:1000]).lower()

        # Check 1: Employer-style employment signals
        employer_signals = ['w-2', 'must be employee', 'employment agreement',
                            'non-compete', 'exclusive', 'full-time only',
                            'payroll', 'direct hire']
        for signal in employer_signals:
            if signal in text:
                flags.append(f"疑似雇佣关系: 包含 '{signal}'")
                company_signable = False

        # Check 2: Work authorization requirements
        visa_signals = ['must be authorized to work in',
                        'us citizens only', 'clearance required',
                        'work permit required']
        for signal in visa_signals:
            if signal in text:
                flags.append(f"工作许可限制: 包含 '{signal}'")

        # Check 3: Onsite requirement (complementary to remote check)
        if 'onsite' in text or 'on-site' in text or 'in-office' in text:
            flags.append("要求到场工作")
            company_signable = False

        return {
            'company_signable': company_signable,
            'flags': flags
        }
