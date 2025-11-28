"""
Judge0 Client using official judge0-python library
Handles code execution and result retrieval
"""
import logging
from typing import Dict, List
from judge0 import Client, Submission, StatusID
from config import settings

logger = logging.getLogger(__name__)


class Judge0Client:
    """Client for Judge0 API using official Python library"""
    
    def __init__(self):
        self.client = Client(endpoint=settings.JUDGE0_API_URL)
        logger.info(f"Judge0 client initialized with endpoint: {settings.JUDGE0_API_URL}")
    
    async def start(self):
        """Initialize client (no-op for sync client)"""
        logger.info("Judge0 client ready")
    
    async def stop(self):
        """Close client (no-op for sync client)"""
        logger.info("Judge0 client closed")
    
    async def execute_code(
        self,
        source_code: str,
        language_id: int,
        test_cases: List[Dict]
    ) -> Dict:
        """
        Execute code against multiple test cases
        
        Args:
            source_code: The code to execute
            language_id: Judge0 language ID
            test_cases: List of test case dicts with 'input' and 'expected_output'
            
        Returns:
            Dictionary with results
        """
        results = []
        passed_count = 0
        total_time = 0.0
        total_memory = 0
        compiler_output = ""
        error_message = ""
        
        for test_case in test_cases:
            stdin = test_case.get('input', '')
            expected_output = test_case.get('expected_output', '')
            weight = test_case.get('weight', 1)
            
            try:
                # Create submission using official library
                submission = Submission(
                    source_code=source_code,
                    language_id=language_id,
                    stdin=stdin,
                    expected_output=expected_output
                )
                
                # Submit and wait for result (sync call, but wrapped in async function)
                result = self.client.create_submission(
                    submission,
                    wait=True,
                    max_wait_time=settings.JUDGE0_TIMEOUT
                )
                
                # Parse result
                status_id = result.status.id if result.status else 0
                status_desc = result.status.description if result.status else "Unknown"
                
                # Check if accepted
                passed = status_id == StatusID.ACCEPTED.value
                
                test_result = {
                    'test_case_id': test_case.get('id'),
                    'status': status_desc,
                    'status_id': status_id,
                    'passed': passed,
                    'weight': weight,
                    'time': float(result.time) if result.time else 0,
                    'memory': int(result.memory) if result.memory else 0,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'compile_output': result.compile_output,
                    'expected_output': expected_output
                }
                
                results.append(test_result)
                
                if passed:
                    passed_count += 1
                
                # Accumulate metrics
                if result.time:
                    total_time += float(result.time)
                if result.memory:
                    total_memory += int(result.memory)
                    
                # Capture errors
                if result.compile_output:
                    compiler_output = result.compile_output
                if result.stderr:
                    error_message = result.stderr
                    
            except Exception as e:
                logger.error(f"Error executing test case {test_case.get('id')}: {e}")
                results.append({
                    'test_case_id': test_case.get('id'),
                    'status': 'Error',
                    'status_id': 0,
                    'passed': False,
                    'weight': weight,
                    'error': str(e)
                })
        
        # Calculate final metrics
        total_tests = len(test_cases)
        avg_time = total_time / total_tests if total_tests > 0 else 0
        avg_memory = total_memory / total_tests if total_tests > 0 else 0
        
        # Calculate weighted score
        total_weight = sum(tc.get('weight', 1) for tc in test_cases)
        earned_weight = sum(
            r.get('weight', 1) for r in results if r.get('passed', False)
        )
        score = int((earned_weight / total_weight) * 100) if total_weight > 0 else 0
        
        return {
            'passed_tests': passed_count,
            'total_tests': total_tests,
            'score': score,
            'execution_time': avg_time,
            'memory_used': avg_memory,
            'test_results': results,
            'compiler_output': compiler_output,
            'error_message': error_message,
            'status': 'completed' if passed_count > 0 else 'failed'
        }
