#!/usr/bin/env python3
"""
Auto Error Fixer - Automatically detects and fixes errors in the application
"""

import os
import sys
import re
import subprocess
import logging
import time
import json
import ast
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AutoErrorFixer:
    """Automatically detects and fixes common errors"""
    
    def __init__(self):
        self.error_log = []
        self.fixed_count = 0
        self.project_root = Path(__file__).parent
        self.main_file = self.project_root / "kinva_master.py"
        
    def detect_errors(self) -> List[Dict]:
        """Detect errors in the application"""
        errors = []
        
        # Check for missing imports
        import_errors = self.detect_missing_imports()
        errors.extend(import_errors)
        
        # Check for syntax errors
        syntax_errors = self.detect_syntax_errors()
        errors.extend(syntax_errors)
        
        # Check for indentation errors
        indent_errors = self.detect_indentation_errors()
        errors.extend(indent_errors)
        
        # Check for runtime errors from logs
        runtime_errors = self.detect_runtime_errors()
        errors.extend(runtime_errors)
        
        # Check for configuration errors
        config_errors = self.detect_config_errors()
        errors.extend(config_errors)
        
        return errors
    
    def detect_missing_imports(self) -> List[Dict]:
        """Detect missing imports"""
        errors = []
        try:
            with open(self.main_file, 'r') as f:
                content = f.read()
            
            # Find all import statements
            imports = re.findall(r'^(?:from|import)\s+([a-zA-Z0-9_\.]+)', content, re.MULTILINE)
            
            for imp in imports:
                imp_name = imp.split('.')[0]
                try:
                    __import__(imp_name)
                except ImportError:
                    errors.append({
                        'type': 'missing_import',
                        'module': imp_name,
                        'message': f"Missing import: {imp_name}",
                        'fix': f"pip install {imp_name}"
                    })
        except Exception as e:
            logger.error(f"Error detecting missing imports: {e}")
        
        return errors
    
    def detect_syntax_errors(self) -> List[Dict]:
        """Detect syntax errors in Python code"""
        errors = []
        try:
            with open(self.main_file, 'r') as f:
                content = f.read()
            
            try:
                ast.parse(content)
            except SyntaxError as e:
                errors.append({
                    'type': 'syntax_error',
                    'line': e.lineno,
                    'message': str(e),
                    'text': content.split('\n')[e.lineno - 1] if e.lineno else '',
                    'fix': self.suggest_syntax_fix(e)
                })
        except Exception as e:
            logger.error(f"Error detecting syntax errors: {e}")
        
        return errors
    
    def detect_indentation_errors(self) -> List[Dict]:
        """Detect indentation errors"""
        errors = []
        try:
            with open(self.main_file, 'r') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines, 1):
                # Check for mixed tabs and spaces
                if '\t' in line and '    ' in line:
                    errors.append({
                        'type': 'mixed_indentation',
                        'line': i,
                        'message': 'Mixed tabs and spaces detected',
                        'fix': 'Replace tabs with spaces (4 spaces per indent)'
                    })
                
                # Check for unexpected indent
                if line.startswith('    @') and i > 1 and not lines[i-2].strip().endswith(':'):
                    errors.append({
                        'type': 'unexpected_indent',
                        'line': i,
                        'message': f'Unexpected indent at line {i}',
                        'text': line.strip(),
                        'fix': 'Remove extra spaces before decorator'
                    })
        except Exception as e:
            logger.error(f"Error detecting indentation errors: {e}")
        
        return errors
    
    def detect_runtime_errors(self) -> List[Dict]:
        """Detect runtime errors from logs"""
        errors = []
        log_file = self.project_root / "logs" / "app.log"
        
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    content = f.read()
                
                # Common error patterns
                patterns = [
                    (r'ModuleNotFoundError: No module named (\S+)', 'missing_module'),
                    (r'IndentationError: unexpected indent', 'indentation'),
                    (r'SyntaxError: (.+)', 'syntax'),
                    (r'ImportError: (.+)', 'import'),
                    (r'NameError: name (\S+) is not defined', 'name_error'),
                    (r'TypeError: (.+)', 'type_error'),
                    (r'ValueError: (.+)', 'value_error'),
                    (r'KeyError: (.+)', 'key_error'),
                    (r'AttributeError: (.+)', 'attribute_error'),
                ]
                
                for pattern, error_type in patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        errors.append({
                            'type': error_type,
                            'message': str(match),
                            'fix': self.suggest_runtime_fix(error_type, match)
                        })
            except Exception as e:
                logger.error(f"Error detecting runtime errors: {e}")
        
        return errors
    
    def detect_config_errors(self) -> List[Dict]:
        """Detect configuration errors"""
        errors = []
        
        # Check .env file
        env_file = self.project_root / ".env"
        if not env_file.exists():
            errors.append({
                'type': 'missing_env',
                'message': '.env file not found',
                'fix': 'Create .env file with BOT_TOKEN and other variables'
            })
        
        # Check required environment variables
        required_vars = ['BOT_TOKEN', 'ADMIN_IDS']
        if env_file.exists():
            with open(env_file, 'r') as f:
                content = f.read()
                for var in required_vars:
                    if var not in content:
                        errors.append({
                            'type': 'missing_env_var',
                            'message': f'Missing {var} in .env',
                            'fix': f'Add {var}=your_value to .env'
                        })
        
        return errors
    
    def suggest_syntax_fix(self, error) -> str:
        """Suggest fix for syntax error"""
        error_msg = str(error)
        
        if "f-string" in error_msg and "invalid syntax" in error_msg:
            return "Convert f-string to regular string with .format() or concatenation"
        elif "unexpected indent" in error_msg:
            return "Remove extra spaces/tabs at the beginning of the line"
        elif "expected an indented block" in error_msg:
            return "Add proper indentation after colon"
        elif "EOL while scanning string literal" in error_msg:
            return "Add missing closing quote"
        else:
            return "Review syntax at the indicated line"
    
    def suggest_runtime_fix(self, error_type: str, match) -> str:
        """Suggest fix for runtime error"""
        fixes = {
            'missing_module': f"Install missing module: pip install {match}",
            'indentation': "Fix indentation (use 4 spaces, no tabs)",
            'syntax': f"Fix syntax error: {match}",
            'import': f"Check import statement: {match}",
            'name_error': f"Define '{match}' before using it",
            'type_error': "Check variable types and conversions",
            'value_error': "Check input values",
            'key_error': "Check if key exists before accessing",
            'attribute_error': "Check if object has the attribute"
        }
        return fixes.get(error_type, "Check error logs for details")
    
    def fix_errors(self, errors: List[Dict]) -> Dict:
        """Automatically fix detected errors"""
        fixes_applied = []
        failed_fixes = []
        
        for error in errors:
            try:
                if error['type'] == 'missing_import':
                    result = self.fix_missing_import(error['module'])
                    if result:
                        fixes_applied.append(f"Installed {error['module']}")
                    else:
                        failed_fixes.append(error['module'])
                
                elif error['type'] == 'indentation':
                    result = self.fix_indentation_error(error)
                    if result:
                        fixes_applied.append(f"Fixed indentation at line {error['line']}")
                    else:
                        failed_fixes.append(f"indentation at line {error['line']}")
                
                elif error['type'] == 'missing_env':
                    result = self.create_env_file()
                    if result:
                        fixes_applied.append("Created .env file")
                    else:
                        failed_fixes.append("create .env")
                
                elif error['type'] == 'syntax_error':
                    result = self.fix_syntax_error(error)
                    if result:
                        fixes_applied.append(f"Fixed syntax at line {error['line']}")
                    else:
                        failed_fixes.append(f"syntax at line {error['line']}")
            
            except Exception as e:
                logger.error(f"Error fixing {error['type']}: {e}")
                failed_fixes.append(error['type'])
        
        return {
            'total_errors': len(errors),
            'fixed': len(fixes_applied),
            'failed': len(failed_fixes),
            'fixes_applied': fixes_applied,
            'failed_fixes': failed_fixes,
            'timestamp': datetime.now().isoformat()
        }
    
    def fix_missing_import(self, module: str) -> bool:
        """Install missing module"""
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', module], 
                          capture_output=True, check=True)
            logger.info(f"Installed {module}")
            return True
        except Exception as e:
            logger.error(f"Failed to install {module}: {e}")
            return False
    
    def fix_indentation_error(self, error: Dict) -> bool:
        """Fix indentation errors"""
        try:
            with open(self.main_file, 'r') as f:
                lines = f.readlines()
            
            if error['line'] <= len(lines):
                line = lines[error['line'] - 1]
                # Remove extra spaces before decorator
                if '@' in line:
                    # Keep only 4 spaces max
                    lines[error['line'] - 1] = '    ' + line.lstrip()
                    
                    with open(self.main_file, 'w') as f:
                        f.writelines(lines)
                    return True
            return False
        except Exception as e:
            logger.error(f"Failed to fix indentation: {e}")
            return False
    
    def create_env_file(self) -> bool:
        """Create .env file with defaults"""
        try:
            env_content = """# Bot Configuration
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_IDS=123456789

# Database
DATABASE_URL=sqlite+aiosqlite:///data/kinva.db
REDIS_URL=redis://localhost:6379

# App Settings
APP_URL=https://your-app.onrender.com
DEBUG=False
"""
            with open(self.project_root / ".env", 'w') as f:
                f.write(env_content)
            logger.info("Created .env file")
            return True
        except Exception as e:
            logger.error(f"Failed to create .env: {e}")
            return False
    
    def fix_syntax_error(self, error: Dict) -> bool:
        """Fix syntax errors in code"""
        try:
            with open(self.main_file, 'r') as f:
                lines = f.readlines()
            
            if error['line'] <= len(lines):
                line = lines[error['line'] - 1]
                
                # Fix f-string syntax
                if 'f-string' in error['message']:
                    # Convert to regular string
                    lines[error['line'] - 1] = line.replace('f"', '"').replace("f'", "'")
                    
                    with open(self.main_file, 'w') as f:
                        f.writelines(lines)
                    return True
                
                # Fix missing colon
                if ':' not in line and 'def ' in line or 'class ' in line:
                    lines[error['line'] - 1] = line.rstrip() + ':\n'
                    with open(self.main_file, 'w') as f:
                        f.writelines(lines)
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Failed to fix syntax: {e}")
            return False
    
    def auto_detect_and_fix(self) -> Dict:
        """Main function to auto-detect and fix errors"""
        logger.info("Starting auto error detection...")
        
        errors = self.detect_errors()
        
        if not errors:
            logger.info("No errors detected!")
            return {
                'status': 'success',
                'message': 'No errors found',
                'errors_found': 0,
                'fixed': 0,
                'timestamp': datetime.now().isoformat()
            }
        
        logger.info(f"Detected {len(errors)} errors")
        for error in errors:
            logger.warning(f"Error: {error['type']} - {error['message']}")
        
        result = self.fix_errors(errors)
        
        logger.info(f"Fixed {result['fixed']} errors, {result['failed']} failed")
        
        return {
            'status': 'completed',
            'errors_found': len(errors),
            'fixed': result['fixed'],
            'failed': result['failed'],
            'fixes_applied': result['fixes_applied'],
            'failed_fixes': result['failed_fixes'],
            'timestamp': datetime.now().isoformat()
        }
    
    def monitor_and_fix_continuous(self, interval: int = 60):
        """Continuously monitor and fix errors"""
        import time
        
        while True:
            try:
                result = self.auto_detect_and_fix()
                if result['errors_found'] > 0:
                    logger.info(f"Auto-fix completed: {result['fixed']} fixes applied")
                
                time.sleep(interval)
            except KeyboardInterrupt:
                logger.info("Monitoring stopped")
                break
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                time.sleep(interval)

# ================================================================
# MAIN EXECUTION
# ================================================================

if __name__ == "__main__":
    fixer = AutoErrorFixer()
    
    # Run once
    result = fixer.auto_detect_and_fix()
    print(json.dumps(result, indent=2))
    
    # Or run continuous monitoring
    # fixer.monitor_and_fix_continuous(interval=60)
