"""
Judge0 Client using judge0-python library
Handles code execution and result retrieval
"""
import logging
from typing import Dict, List
import judge0
from config import settings

logger = logging.getLogger(__name__)

# Judge0 Status IDs
# https://github.com/judge0/judge0/blob/master/db/seeds.rb
STATUS_ACCEPTED = 3
STATUS_WRONG_ANSWER = 4
STATUS_TIME_LIMIT_EXCEEDED = 5
STATUS_COMPILATION_ERROR = 6
STATUS_RUNTIME_ERROR = 7


class Judge0Client:
    """Client for Judge0 API using judge0-python library"""
    
    def __init__(self):
        self.base_url = settings.JUDGE0_API_URL
        logger.info(f"Judge0 client initialized with endpoint: {self.base_url}")
    
    async def start(self):
        """Initialize client"""
        logger.info("Judge0 client ready")
    
    async def stop(self):
        """Close client"""
        logger.info("Judge0 client closed")
    
    async def execute_code(
        self,
        source_code: str,
        language_id: int,
        test_cases: List[Dict]
    ) -> Dict:
        """
        Execute code against multiple test cases using Judge0
        
        Args:
            source_code: The code to execute
            language_id: Judge0 language ID
            test_cases: List of test case dicts with 'input' and 'expected_output'
            
        Returns:
            Dictionary with results
        """
        # Prepare test cases in the format judge0.run() expects
        formatted_test_cases = [
            {
                "input": tc.get('input', ''),
                "expected_output": tc.get('expected_output', '')
            }
            for tc in test_cases
        ]
        
        try:
            # Execute code using judge0.run()
            logger.debug(f"Running code with {len(formatted_test_cases)} test cases")
            results = judge0.run(
                source_code=source_code,
                language_id=language_id,
                test_cases=formatted_test_cases,
                base_url=self.base_url
            )
            
            # Process results
            test_results = []
            passed_count = 0
            compiler_output = ""
            error_message = ""
            
            for i, result in enumerate(results):
                test_case = test_cases[i]
                
                # Get status - judge0 library's Status object can be compared directly
                # Status has __int__ method that returns the status ID
                # 3 = Accepted, 4 = Wrong Answer, etc.
                try:
                    status_id = int(result.status)
                    status_name = result.status.name if hasattr(result.status, 'name') else str(result.status)
                except (ValueError, AttributeError):
                    status_id = 0
                    status_name = 'Unknown'
                
                # Check if passed (status ID 3 = Accepted)
                passed = status_id == STATUS_ACCEPTED
                
                test_result = {
                    'test_id': test_case.get('id'),
                    'status': status_name,
                    'passed': passed,
                    'execution_time': float(result.time) if result.time else 0.0,
                    'memory_usage': int(result.memory) if result.memory else 0,
                    'error_message': result.stderr or result.compile_output or None
                }
                
                test_results.append(test_result)
                
                if passed:
                    passed_count += 1
                
                # Capture errors
                if result.compile_output:
                    compiler_output = result.compile_output
                if result.stderr:
                    error_message = result.stderr
            
            # Calculate score
            total_tests = len(test_cases)
            score = int((passed_count / total_tests) * 100) if total_tests > 0 else 0
            
            return {
                'passed_tests': passed_count,
                'total_tests': total_tests,
                'score': score,
                'test_results': test_results,
                'error_message': error_message or compiler_output,
                'status': 'completed' if passed_count > 0 else 'failed'
            }
            
        except Exception as e:
            logger.error(f"Error executing code with judge0.run(): {e}", exc_info=True)
            # Return error result
            return {
                'passed_tests': 0,
                'total_tests': len(test_cases),
                'score': 0,
                'test_results': [
                    {
                        'test_id': tc.get('id'),
                        'status': 'Error',
                        'passed': False,
                        'error_message': str(e)
                    }
                    for tc in test_cases
                ],
                'error_message': str(e),
                'status': 'failed'
            }
