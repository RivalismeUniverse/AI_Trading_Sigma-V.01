"""
AWS Bedrock Client for Claude AI
Complete implementation for AI TRADING SIGMA 
"""
import boto3
import json
from typing import Optional
from botocore.config import Config
import asyncio

class BedrockClient:
    """AWS Bedrock client for Claude API integration"""
    
    def __init__(
        self,
        aws_access_key: str,
        aws_secret_key: str,
        region: str = "us-east-1",
        model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    ):
        self.model_id = model_id
        self.region = region
        
        # Configure boto3 with retries
        config = Config(
            region_name=region,
            retries={'max_attempts': 3, 'mode': 'adaptive'}
        )
        
        # Initialize Bedrock client
        self.client = boto3.client(
            service_name='bedrock-runtime',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            config=config
        )
        
        print(f"✅ Bedrock client initialized - Region: {region}, Model: {model_id}")
    
    async def invoke_claude(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> str:
        """
        Invoke Claude via AWS Bedrock
        
        Args:
            prompt: User prompt/question
            system_prompt: System instruction (optional)
            max_tokens: Maximum response tokens
            temperature: Response randomness (0-1)
            
        Returns:
            Claude's response text
        """
        try:
            # Prepare request body
            messages = [{"role": "user", "content": prompt}]
            
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages
            }
            
            if system_prompt:
                body["system"] = system_prompt
            
            # Invoke Bedrock (sync call, wrapped in async)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps(body)
                )
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            # Extract text
            if 'content' in response_body and len(response_body['content']) > 0:
                text = response_body['content'][0]['text']
                print(f"✅ Bedrock response: {len(text)} characters")
                return text
            else:
                print(f"⚠️ Unexpected response format: {response_body}")
                return ""
            
        except Exception as e:
            print(f"❌ Bedrock invocation error: {e}")
            return ""
    
    async def test_connection(self) -> bool:
        """Test Bedrock connection"""
        try:
            print("🧪 Testing Bedrock connection...")
            
            response = await self.invoke_claude(
                prompt="Reply with just 'OK' if you can read this.",
                max_tokens=10,
                temperature=0
            )
            
            if response and ("OK" in response or "ok" in response.lower()):
                print("✅ Bedrock connection successful!")
                return True
            else:
                print(f"⚠️ Unexpected response: {response}")
                return False
                
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate API cost for Bedrock Claude
        
        Bedrock Pricing (as of 2024):
        - Input: $0.003 per 1K tokens
        - Output: $0.015 per 1K tokens
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Estimated cost in USD
        """
        input_cost = (input_tokens / 1000) * 0.003
        output_cost = (output_tokens / 1000) * 0.015
        total_cost = input_cost + output_cost
        
        return round(total_cost, 4)


# Test code
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    async def test():
        client = BedrockClient(
            aws_access_key=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region=os.getenv('AWS_REGION', 'us-east-1')
        )
        
        # Test connection
        success = await client.test_connection()
        
        if success:
            # Test actual query
            response = await client.invoke_claude(
                prompt="Explain what is scalping in trading in one sentence.",
                max_tokens=100
            )
            print(f"\n📝 Response: {response}")
            
            # Estimate cost
            cost = client.estimate_cost(input_tokens=20, output_tokens=50)
            print(f"\n💰 Estimated cost for this call: ${cost}")
    
    asyncio.run(test())
