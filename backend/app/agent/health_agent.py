import os
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pinai_agent_sdk import PINAIAgentSDK, AGENT_CATEGORY_DAILY

# Import from agent_marketplace for compatibility with the SDK pattern
try:
    from agent_marketplace.agents.ai_agent import AI_Agent
    from agent_marketplace.agents.personal_ai import CHECK_CHAT_STATE_PROMPT
    from agent_marketplace.schemas.agents import Message
    from agent_marketplace.config import get_settings
except ImportError:
    # Define fallback classes if the imports aren't available
    class AI_Agent:
        def __init__(self, name, owner, description, model_config={}):
            self.name = name
            self.owner = owner
            self.description = description
            self.model_config = model_config
            self.context = type('Context', (), {'history': []})
            self.task_complete = False
    
    class Message:
        def __init__(self, role, content, sender, receiver, timestamp, metadata={}):
            self.role = role
            self.content = content
            self.sender = sender
            self.receiver = receiver
            self.timestamp = timestamp
            self.metadata = metadata
    
    # Fallback prompt template
    CHECK_CHAT_STATE_PROMPT = """
    You are {agent_name}, owned by {owner}.
    
    Your task is to determine if the conversation with the user should end or continue.
    
    User intent: {user_intent}
    
    Your description: {service_agent_description}
    
    Conversation history:
    {conversation_history}
    
    Based on the conversation history, has the user's intent been fully addressed?
    If yes, respond with "[CONVERSATION_ENDS]". If no, respond with "[CONTINUE]".
    """

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class HealthAIAgent(AI_Agent):
    """
    Health AI Agent using the PinAI SDK to provide health insights and recommendations
    based on user's personal health data.
    """
    
    def __init__(self, name="Health AI Assistant Yash Testing", owner="HealthAI", 
                 description="Personal health assistant that analyzes your health data and provides insights and recommendations",
                 user_intent="Get health insights and recommendations", model_config={}):
        """Initialize the Health AI Agent."""
        super().__init__(name, owner, description, model_config)
        
        # Get API key from environment variable
        self.api_key = os.getenv("PINAI_API_KEY", "")
        self.agent_id = os.getenv("PINAI_AGENT_ID", None)
        self.user_intent = user_intent
        
        # Initialize the PinAI SDK client
        self.sdk_client = self._initialize_sdk_client()
        
        # Register agent if no agent_id is available
        if not self.agent_id and self.sdk_client:
            self._register_agent()
        
        # Store sessions and health data mapping
        self.sessions = {}
    
    def _initialize_sdk_client(self) -> Optional[PINAIAgentSDK]:
        """Initialize the PinAI SDK client."""
        try:
            if not self.api_key:
                logger.warning("PINAI_API_KEY environment variable not set. Some features may not work.")
                return None
            return PINAIAgentSDK(api_key=self.api_key)
        except Exception as e:
            logger.error(f"Failed to initialize PinAI SDK client: {e}")
            return None
    
    def _register_agent(self) -> None:
        """Register the Health AI Agent with PinAI platform."""
        if not self.sdk_client:
            logger.error("Cannot register agent: SDK client not initialized")
            return
        
        try:
            agent_info = self.sdk_client.register_agent(
                name=self.name,
                description=self.description,
                category=AGENT_CATEGORY_DAILY,
            )
            
            self.agent_id = agent_info.get("id")
            logger.info(f"Registered Health AI Agent with ID: {self.agent_id}")
            
            # Save agent_id for future use
            os.environ["PINAI_AGENT_ID"] = str(self.agent_id)
        except Exception as e:
            logger.error(f"Failed to register agent: {e}")
            
            # Check if error is due to name conflict and try to get the existing agent ID
            if "already exists" in str(e):
                try:
                    # Try to find the agent by name using list_agents method if available
                    logger.info(f"Attempting to find existing agent with name: {self.name}")
                    
                    try:
                        agents = self.sdk_client.list_agents()
                        for agent in agents:
                            if agent.get("name") == self.name:
                                self.agent_id = agent.get("id")
                                logger.info(f"Found existing agent with ID: {self.agent_id}")
                                os.environ["PINAI_AGENT_ID"] = str(self.agent_id)
                                return
                    except Exception as list_error:
                        # If list_agents doesn't exist or fails, try a workaround
                        # Create a slightly different name to see if we can extract the ID from the error
                        logger.warning(f"Couldn't list agents: {list_error}. Using fallback method.")
                        
                        # Generate a unique name by adding a timestamp
                        temp_name = f"{self.name}_{int(datetime.now().timestamp())}"
                        try:
                            # This will likely fail with a different error
                            self.sdk_client.register_agent(
                                name=temp_name,
                                description=self.description,
                                category=AGENT_CATEGORY_DAILY,
                            )
                        except Exception as temp_error:
                            # If we can extract an ID from the response, use it
                            # This is a last resort fallback
                            logger.warning("Using temp agent creation as fallback")
                            pass
                except Exception as find_error:
                    logger.error(f"Failed to find existing agent: {find_error}")
                    
            # If we couldn't recover, continue without agent ID
            if not self.agent_id:
                logger.warning("Will operate in fallback mode without PinAI agent integration")

    def on_message(self, message: Message, sender: AI_Agent) -> Message:
        """
        Process messages from users and generate responses.
        
        Args:
            message: The incoming message
            sender: The sender of the message
            
        Returns:
            Message: The response message
        """
        # Update context
        if message:
            self.context.history.append(message)

        # Generate response
        health_data = self._get_health_data_from_context(message)
        response = self.generate_response(message, sender, health_data)
        
        # Create return message
        return_message = Message(
            role="assistant", 
            content=response.get("text", "I'm here to help with your health questions."), 
            sender=self.name, 
            receiver=sender.name,
            timestamp=datetime.now(), 
            metadata=response.get("metadata", {})
        )

        # Update context
        self.context.history.append(return_message)

        # Check if the task is complete
        chat_state = self.llm_call_to_check_chat_state()
        if chat_state.get("content") == "[CONVERSATION_ENDS]":
            self.task_complete = True

        return return_message
    
    def _get_health_data_from_context(self, message: Message) -> Dict[str, Any]:
        """
        Extract health data from message context or metadata.
        
        Args:
            message: The incoming message
            
        Returns:
            Dict[str, Any]: Health data
        """
        # Try to get health data from metadata
        if hasattr(message, 'metadata') and message.metadata:
            if isinstance(message.metadata, dict) and 'health_data' in message.metadata:
                try:
                    if isinstance(message.metadata['health_data'], str):
                        return json.loads(message.metadata['health_data'])
                    return message.metadata['health_data']
                except Exception as e:
                    logger.error(f"Error parsing health data from metadata: {e}")
        
        # If no health data in metadata, check the session
        if hasattr(message, 'sender') and message.sender:
            session_id = f"session_{message.sender}"
            if session_id in self.sessions and 'health_data' in self.sessions[session_id]:
                return self.sessions[session_id]['health_data']
        
        # Return empty health data if none found
        return {
            "user": {},
            "bloodTests": [],
            "vitals": [],
            "medicalHistory": {},
            "healthMetrics": {}
        }
    
    def generate_response(self, message: Message, sender: AI_Agent, health_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a response to the user message.
        
        Args:
            message: User message
            sender: Message sender
            health_data: User health data
            
        Returns:
            Dict[str, Any]: Response with text and metadata
        """
        # Skip processing if message is empty
        if not message or not message.content:
            return {"text": "I'm here to help with your health questions. What would you like to know?"}
        
        # Check if conversation should end based on context
        chat_state = self.llm_call_to_check_chat_state()
        if chat_state.get("content") == "[CONVERSATION_ENDS]":
            self.task_complete = True
            return {"text": "Is there anything else I can help you with regarding your health?"}
        
        # Try to use PinAI SDK if available
        if self.sdk_client and self.agent_id:
            try:
                # Start the agent if needed
                self.sdk_client.start(
                    on_message_callback=lambda agent_message: agent_message['content'],
                    agent_id=self.agent_id
                )
                
                # Convert health data to string for metadata if needed
                health_data_str = json.dumps(health_data) if isinstance(health_data, dict) else health_data
                
                # Send message to agent
                response = self.sdk_client.send_message(
                    content=message.content,
                    session_id=f"session_{sender.name}" if hasattr(sender, 'name') else "default_session",
                    meta_data={"health_data": health_data_str}
                )
                
                if response:
                    return {"text": response, "metadata": {"source": "pinai_sdk"}}
            except Exception as e:
                logger.error(f"Error using PinAI SDK: {e}")
        
        # Fallback to rule-based responses if PinAI failed or isn't available
        return self._generate_rule_based_response(message.content, health_data)
    
    def _generate_rule_based_response(self, message_text: str, health_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a rule-based response when PinAI SDK is unavailable.
        
        Args:
            message_text: Text of the user message
            health_data: User health data
            
        Returns:
            Dict[str, Any]: Response with text and metadata
        """
        message_lower = message_text.lower()
        
        # Check message intent - more specific cases first
        if any(term in message_lower for term in ["cholesterol", "cholestrol", "ldl", "hdl", "triglycerides", "lipids"]):
            response_text = self._analyze_cholesterol(health_data.get("bloodTests", []))
            return {"text": response_text, "metadata": {"analysis_type": "cholesterol"}}
        
        elif any(term in message_lower for term in ["glucose", "sugar", "diabetes", "a1c"]):
            response_text = self._analyze_glucose(health_data.get("bloodTests", []))
            return {"text": response_text, "metadata": {"analysis_type": "glucose"}}
        
        elif any(term in message_lower for term in ["vitamin", "minerals", "deficiency"]):
            response_text = self._analyze_vitamins(health_data.get("bloodTests", []))
            return {"text": response_text, "metadata": {"analysis_type": "vitamins"}}
        
        elif any(term in message_lower for term in ["blood test", "blood work", "lab"]):
            response_text = self._analyze_blood_test(health_data.get("bloodTests", []))
            return {"text": response_text, "metadata": {"analysis_type": "blood_tests"}}
        
        elif any(term in message_lower for term in ["vital", "blood pressure", "heart rate", "temperature"]):
            response_text = self._analyze_vitals(health_data.get("vitals", []))
            return {"text": response_text, "metadata": {"analysis_type": "vitals"}}
        
        elif any(term in message_lower for term in ["recommend", "advice", "suggestion", "should i"]):
            response_text = self._generate_health_recommendations(health_data)
            return {"text": response_text, "metadata": {"analysis_type": "recommendations"}}
        
        elif any(term in message_lower for term in ["health status", "health overview", "my health", "summary"]):
            blood_analysis = self._analyze_blood_test(health_data.get("bloodTests", []))
            vitals_analysis = self._analyze_vitals(health_data.get("vitals", []))
            response_text = f"Health Overview:\n\n{blood_analysis}\n\n{vitals_analysis}"
            return {"text": response_text, "metadata": {"analysis_type": "overview"}}
        
        elif any(term in message_lower for term in ["sleep", "rest", "insomnia"]):
            response_text = self._analyze_sleep(health_data.get("healthMetrics", {}).get("sleepData", []))
            return {"text": response_text, "metadata": {"analysis_type": "sleep"}}
        
        # Default response
        return {
            "text": "I'm your Health AI Assistant. I can help analyze your blood tests, vital signs, sleep patterns, and provide health recommendations. What would you like to know about your health?",
            "metadata": {"analysis_type": "general"}
        }
    
    def llm_call_to_check_chat_state(self) -> Dict[str, Any]:
        """
        Check if the agent should complete the chat at this turn. 
        If to complete chat, return "[CONVERSATION_ENDS]", otherwise return "[CONTINUE]".
        """
        if not self.context.history:
            return {"content": "[CONTINUE]"}
        
        conversation_history = "\n".join([f"{msg.sender}: {msg.content}" for msg in self.context.history][-10:])

        prompt = CHECK_CHAT_STATE_PROMPT.format(
            agent_name=self.name,
            owner=self.owner,
            user_intent=self.user_intent,
            service_agent_description=self.description,
            conversation_history=conversation_history,
        )

        # Try to use PinAI SDK for this if available
        if self.sdk_client:
            try:
                response = self.sdk_client.send_message(
                    content=prompt,
                    session_id="check_chat_state",
                    meta_data={"is_system": True}
                )
                if response:
                    return {"content": "[CONVERSATION_ENDS]" if "[CONVERSATION_ENDS]" in response else "[CONTINUE]"}
            except Exception:
                pass
        
        # Fallback to simple heuristic
        if any(term in conversation_history.lower() for term in ["goodbye", "thank you", "thanks", "bye"]):
            return {"content": "[CONVERSATION_ENDS]"}
        return {"content": "[CONTINUE]"}
    
    def _analyze_blood_test(self, blood_tests: List[Dict[str, Any]]) -> str:
        """
        Analyze blood test results to identify abnormal values and provide insights.
        
        Args:
            blood_tests: List of blood test results
            
        Returns:
            str: Analysis of blood test results
        """
        if not blood_tests or len(blood_tests) == 0:
            return "No blood test data available for analysis."
        
        # Get most recent blood test
        latest_test = blood_tests[0]
        
        # Find abnormal results
        abnormal_results = []
        for test_name, test_data in latest_test["results"].items():
            if test_data.get("status") != "normal":
                abnormal_results.append({
                    "name": test_name,
                    "value": test_data["value"],
                    "unit": test_data["unit"],
                    "normal_range": test_data["normalRange"],
                    "status": test_data["status"]
                })
        
        # Generate analysis
        analysis = f"Blood Test Analysis (from {latest_test['date']}):\n\n"
        
        if not abnormal_results:
            analysis += "All test results are within normal ranges. Your blood work looks healthy!"
        else:
            analysis += f"Found {len(abnormal_results)} test result(s) outside normal ranges:\n\n"
            
            for result in abnormal_results:
                analysis += f"- {result['name']}: {result['value']} {result['unit']} "
                analysis += f"(Normal range: {result['normal_range']}, Status: {result['status']})\n"
            
            # Add specific insights for common abnormal results
            for result in abnormal_results:
                if result["name"] == "glucose" and result["status"] == "elevated":
                    analysis += "\nYour glucose level is elevated. This may indicate prediabetes or "
                    analysis += "could be due to recent food intake before the test. Consider follow-up testing "
                    analysis += "and consulting with your doctor about lifestyle modifications like diet changes "
                    analysis += "and increased physical activity."
                
                elif result["name"] == "cholesterolTotal" and result["status"] == "elevated":
                    analysis += "\nYour total cholesterol is elevated. This increases risk for heart disease "
                    analysis += "and stroke. Consider dietary changes (reducing saturated fats), regular exercise, "
                    analysis += "and possibly medication if recommended by your doctor."
                
                elif result["name"] == "cholesterolLDL" and result["status"] == "elevated":
                    analysis += "\nYour LDL ('bad') cholesterol is elevated. This can lead to plaque buildup "
                    analysis += "in your arteries. Consider reducing saturated and trans fats in your diet, "
                    analysis += "increasing fiber intake, and regular exercise."
                
                elif result["name"] == "triglycerides" and result["status"] == "elevated":
                    analysis += "\nYour triglyceride levels are elevated. This may increase risk of heart disease. "
                    analysis += "Consider limiting added sugars and simple carbohydrates, reducing alcohol intake, "
                    analysis += "and increasing physical activity."
                
                elif result["name"] == "vitaminD" and result["status"] == "deficient":
                    analysis += "\nYou have vitamin D deficiency. This can affect bone health and immune function. "
                    analysis += "Consider more sun exposure (safely), vitamin D-rich foods like fatty fish, "
                    analysis += "and supplements as recommended by your doctor."
        
        return analysis
    
    def _analyze_vitals(self, vitals: List[Dict[str, Any]]) -> str:
        """
        Analyze vital signs to provide insights.
        
        Args:
            vitals: List of vital sign measurements
            
        Returns:
            str: Analysis of vital signs
        """
        if not vitals or len(vitals) == 0:
            return "No vital sign data available for analysis."
        
        # Get most recent vitals
        latest_vitals = vitals[0]
        
        # Generate analysis
        analysis = f"Vital Signs Analysis (from {latest_vitals['date']}):\n\n"
        
        # Blood pressure analysis
        bp = latest_vitals["bloodPressure"]
        analysis += f"Blood Pressure: {bp['systolic']}/{bp['diastolic']} mmHg ({bp['status']})\n"
        
        if bp['status'] == "elevated":
            analysis += "Your blood pressure is elevated. This may increase risk for heart disease and stroke. "
            analysis += "Consider reducing sodium intake, regular exercise, stress management, "
            analysis += "and maintaining a healthy weight.\n\n"
        else:
            analysis += "Your blood pressure is within normal range.\n\n"
        
        # Heart rate analysis
        hr = latest_vitals["heartRate"]
        analysis += f"Heart Rate: {hr['value']} {hr['unit']} ({hr['status']})\n"
        
        # Oxygen saturation analysis
        ox = latest_vitals["oxygenSaturation"]
        analysis += f"Oxygen Saturation: {ox['value']}{ox['unit']} ({ox['status']})\n"
        
        # Temperature analysis
        temp = latest_vitals["temperature"]
        analysis += f"Body Temperature: {temp['value']} {temp['unit']} ({temp['status']})\n"
        
        return analysis
    
    def _analyze_sleep(self, sleep_data: List[Dict[str, Any]]) -> str:
        """
        Analyze sleep data to provide insights.
        
        Args:
            sleep_data: List of sleep records
            
        Returns:
            str: Analysis of sleep patterns
        """
        if not sleep_data or len(sleep_data) == 0:
            return "No sleep data available for analysis."
        
        # Calculate average sleep metrics
        avg_total = sum(day["totalHours"] for day in sleep_data) / len(sleep_data)
        avg_deep = sum(day["deepSleepHours"] for day in sleep_data) / len(sleep_data)
        avg_rem = sum(day["remSleepHours"] for day in sleep_data) / len(sleep_data)
        
        # Generate analysis
        analysis = f"Sleep Analysis (last {len(sleep_data)} days):\n\n"
        analysis += f"Average Total Sleep: {avg_total:.1f} hours\n"
        analysis += f"Average Deep Sleep: {avg_deep:.1f} hours\n"
        analysis += f"Average REM Sleep: {avg_rem:.1f} hours\n\n"
        
        # Add recommendations based on sleep quality
        if avg_total < 7:
            analysis += "Your average sleep duration is below the recommended 7-9 hours. "
            analysis += "Consider adjusting your sleep schedule to allow for more rest time."
        elif avg_deep < 1.5:
            analysis += "Your deep sleep appears to be lower than optimal. Deep sleep is essential "
            analysis += "for physical recovery. Consider limiting caffeine/alcohol, maintaining a "
            analysis += "regular sleep schedule, and ensuring your sleep environment is comfortable."
        else:
            analysis += "Your overall sleep patterns look good. Keep maintaining a consistent "
            analysis += "sleep schedule and healthy sleep habits."
        
        return analysis
    
    def _generate_health_recommendations(self, health_data: Dict[str, Any]) -> str:
        """
        Generate personalized health recommendations based on user's health data.
        
        Args:
            health_data: User's health data
            
        Returns:
            str: Personalized health recommendations
        """
        recommendations = "Personalized Health Recommendations:\n\n"
        
        # Check blood tests for recommendations
        blood_tests = health_data.get("bloodTests", [])
        if blood_tests and len(blood_tests) > 0:
            latest_test = blood_tests[0]
            results = latest_test.get("results", {})
            
            # Glucose recommendations
            glucose = results.get("glucose", {})
            if glucose.get("status") == "elevated":
                recommendations += "1. Blood Sugar Management:\n"
                recommendations += "   - Limit added sugars and refined carbohydrates\n"
                recommendations += "   - Increase fiber intake with whole grains, vegetables, and legumes\n"
                recommendations += "   - Regular physical activity (aim for 150 minutes per week)\n"
                recommendations += "   - Consider speaking with a healthcare provider about diabetes screening\n\n"
            
            # Cholesterol recommendations
            chol_total = results.get("cholesterolTotal", {})
            chol_ldl = results.get("cholesterolLDL", {})
            triglycerides = results.get("triglycerides", {})
            
            if (chol_total.get("status") == "elevated" or 
                chol_ldl.get("status") == "elevated" or 
                triglycerides.get("status") == "elevated"):
                recommendations += "2. Cholesterol Management:\n"
                recommendations += "   - Reduce saturated and trans fats (limit red meat, full-fat dairy)\n"
                recommendations += "   - Increase heart-healthy fats (olive oil, avocados, nuts)\n"
                recommendations += "   - Add more soluble fiber (oats, beans, fruits)\n"
                recommendations += "   - Regular physical activity\n"
                recommendations += "   - Consider plant sterols/stanols if recommended\n\n"
            
            # Vitamin D recommendations
            vit_d = results.get("vitaminD", {})
            if vit_d.get("status") == "deficient":
                recommendations += "3. Vitamin D Improvement:\n"
                recommendations += "   - Safe sun exposure (15-30 minutes several times weekly)\n"
                recommendations += "   - Consume vitamin D-rich foods (fatty fish, fortified milk, egg yolks)\n"
                recommendations += "   - Consider a vitamin D supplement (1000-2000 IU daily)\n\n"
        
        # Check vitals for recommendations
        vitals = health_data.get("vitals", [])
        if vitals and len(vitals) > 0:
            latest_vitals = vitals[0]
            bp = latest_vitals.get("bloodPressure", {})
            
            if bp.get("status") == "elevated":
                recommendations += "4. Blood Pressure Management:\n"
                recommendations += "   - Reduce sodium intake (<2300mg daily)\n"
                recommendations += "   - DASH diet (rich in fruits, vegetables, whole grains, lean proteins)\n"
                recommendations += "   - Regular physical activity\n"
                recommendations += "   - Limit alcohol consumption\n"
                recommendations += "   - Stress management techniques\n\n"
        
        # Check health metrics for recommendations
        metrics = health_data.get("healthMetrics", {})
        
        # Sleep recommendations
        sleep_data = metrics.get("sleepData", [])
        if sleep_data and len(sleep_data) > 0:
            avg_hours = sum(day["totalHours"] for day in sleep_data) / len(sleep_data)
            if avg_hours < 7:
                recommendations += "5. Sleep Improvement:\n"
                recommendations += "   - Aim for 7-9 hours of sleep nightly\n"
                recommendations += "   - Maintain a consistent sleep schedule\n"
                recommendations += "   - Create a restful environment (dark, quiet, comfortable)\n"
                recommendations += "   - Limit screen time before bed\n"
                recommendations += "   - Avoid caffeine and large meals before bedtime\n\n"
        
        # General recommendations
        recommendations += "General Health Maintenance:\n"
        recommendations += "   - Stay hydrated (aim for 2-3 liters of water daily)\n"
        recommendations += "   - Balanced diet rich in whole foods\n"
        recommendations += "   - Regular physical activity (150+ minutes moderate activity weekly)\n"
        recommendations += "   - Stress management (meditation, deep breathing, hobbies)\n"
        recommendations += "   - Regular health check-ups and screenings\n"
        
        return recommendations
    
    def _analyze_cholesterol(self, blood_tests: List[Dict[str, Any]]) -> str:
        """
        Analyze cholesterol results to provide detailed insights.
        
        Args:
            blood_tests: List of blood test results
            
        Returns:
            str: Analysis of cholesterol metrics
        """
        if not blood_tests or len(blood_tests) == 0:
            return "No blood test data available for cholesterol analysis."
        
        # Get most recent blood test
        latest_test = blood_tests[0]
        results = latest_test.get("results", {})
        
        # Check if cholesterol data exists
        chol_total = results.get("cholesterolTotal", {})
        chol_ldl = results.get("cholesterolLDL", {})
        chol_hdl = results.get("cholesterolHDL", {})
        triglycerides = results.get("triglycerides", {})
        
        if not (chol_total or chol_ldl or chol_hdl or triglycerides):
            return "No cholesterol data found in your blood test results."
        
        # Generate analysis
        analysis = f"Cholesterol Analysis (from {latest_test['date']}):\n\n"
        
        # Add total cholesterol
        if chol_total:
            analysis += f"Total Cholesterol: {chol_total.get('value', 'N/A')} {chol_total.get('unit', 'mg/dL')} "
            analysis += f"(Status: {chol_total.get('status', 'unknown')})\n"
            analysis += f"Normal Range: {chol_total.get('normalRange', '<200 mg/dL')}\n\n"
            
            if chol_total.get('status') == "elevated":
                analysis += "Your total cholesterol is elevated. This is a measure of all cholesterol types in your blood "
                analysis += "and can increase your risk for heart disease and stroke when high. "
                analysis += "However, it's important to look at the breakdown of HDL vs LDL.\n\n"
            elif chol_total.get('status') == "normal":
                analysis += "Your total cholesterol is within normal range, which is good for heart health.\n\n"
        
        # Add LDL cholesterol
        if chol_ldl:
            analysis += f"LDL (Bad) Cholesterol: {chol_ldl.get('value', 'N/A')} {chol_ldl.get('unit', 'mg/dL')} "
            analysis += f"(Status: {chol_ldl.get('status', 'unknown')})\n"
            analysis += f"Normal Range: {chol_ldl.get('normalRange', '<100 mg/dL')}\n\n"
            
            if chol_ldl.get('status') == "elevated":
                analysis += "Your LDL cholesterol is elevated. LDL is considered the 'bad' cholesterol because it contributes "
                analysis += "to plaque buildup in your arteries, which can increase risk of heart attack and stroke. "
                analysis += "Consider dietary changes like reducing saturated/trans fats, increasing soluble fiber, "
                analysis += "and regular exercise.\n\n"
            elif chol_ldl.get('status') == "normal":
                analysis += "Your LDL cholesterol is within normal range, which is good for cardiovascular health.\n\n"
        
        # Add HDL cholesterol
        if chol_hdl:
            analysis += f"HDL (Good) Cholesterol: {chol_hdl.get('value', 'N/A')} {chol_hdl.get('unit', 'mg/dL')} "
            analysis += f"(Status: {chol_hdl.get('status', 'unknown')})\n"
            analysis += f"Normal Range: {chol_hdl.get('normalRange', '>40 mg/dL for men, >50 mg/dL for women')}\n\n"
            
            if chol_hdl.get('status') == "low":
                analysis += "Your HDL cholesterol is lower than optimal. HDL is considered 'good' cholesterol because it helps "
                analysis += "remove other forms of cholesterol from your bloodstream. Higher levels are generally better. "
                analysis += "Regular exercise, quitting smoking, and maintaining a healthy weight can help increase HDL.\n\n"
            elif chol_hdl.get('status') == "normal" or chol_hdl.get('status') == "optimal":
                analysis += "Your HDL cholesterol is at a good level, which helps protect against heart disease.\n\n"
        
        # Add triglycerides
        if triglycerides:
            analysis += f"Triglycerides: {triglycerides.get('value', 'N/A')} {triglycerides.get('unit', 'mg/dL')} "
            analysis += f"(Status: {triglycerides.get('status', 'unknown')})\n"
            analysis += f"Normal Range: {triglycerides.get('normalRange', '<150 mg/dL')}\n\n"
            
            if triglycerides.get('status') == "elevated":
                analysis += "Your triglycerides are elevated. Triglycerides are a type of fat in your blood that your body "
                analysis += "uses for energy. High levels can contribute to hardening of the arteries and increase risk of "
                analysis += "heart disease, stroke, and pancreatitis. Consider limiting added sugars, refined carbs, and alcohol, "
                analysis += "while increasing physical activity.\n\n"
            elif triglycerides.get('status') == "normal":
                analysis += "Your triglyceride levels are within normal range, which is good for heart health.\n\n"
        
        # Add cholesterol ratio if both values exist
        if chol_total and chol_hdl and chol_total.get('value') and chol_hdl.get('value'):
            try:
                total_val = float(chol_total.get('value'))
                hdl_val = float(chol_hdl.get('value'))
                ratio = total_val / hdl_val
                
                analysis += f"Total Cholesterol to HDL Ratio: {ratio:.1f}\n"
                if ratio < 3.5:
                    analysis += "This ratio is optimal (below 3.5), indicating lower cardiovascular risk.\n\n"
                elif ratio < 5:
                    analysis += "This ratio is good (below 5), but there's room for improvement.\n\n"
                else:
                    analysis += "This ratio is higher than optimal (above 5), indicating increased cardiovascular risk.\n\n"
            except (ValueError, ZeroDivisionError):
                pass
        
        # Add general recommendations
        analysis += "General recommendations for cholesterol management:\n"
        analysis += "- Eat heart-healthy foods (fruits, vegetables, whole grains, lean proteins)\n"
        analysis += "- Limit saturated and trans fats\n"
        analysis += "- Increase intake of omega-3 fatty acids (fatty fish, walnuts, flaxseeds)\n"
        analysis += "- Regular physical activity (aim for 150+ minutes per week)\n"
        analysis += "- Maintain healthy weight\n"
        analysis += "- Limit alcohol consumption\n"
        analysis += "- Quit smoking if applicable\n"
        
        return analysis
    
    def _analyze_glucose(self, blood_tests: List[Dict[str, Any]]) -> str:
        """
        Analyze glucose results to provide detailed insights.
        
        Args:
            blood_tests: List of blood test results
            
        Returns:
            str: Analysis of glucose metrics
        """
        if not blood_tests or len(blood_tests) == 0:
            return "No blood test data available for glucose analysis."
        
        # Get most recent blood test
        latest_test = blood_tests[0]
        results = latest_test.get("results", {})
        
        # Check if glucose data exists
        glucose = results.get("glucose", {})
        a1c = results.get("hba1c", {})
        
        if not (glucose or a1c):
            return "No glucose data found in your blood test results."
        
        # Generate analysis
        analysis = f"Blood Sugar Analysis (from {latest_test['date']}):\n\n"
        
        # Add glucose
        if glucose:
            analysis += f"Fasting Glucose: {glucose.get('value', 'N/A')} {glucose.get('unit', 'mg/dL')} "
            analysis += f"(Status: {glucose.get('status', 'unknown')})\n"
            analysis += f"Normal Range: {glucose.get('normalRange', '70-99 mg/dL')}\n\n"
            
            if glucose.get('status') == "elevated":
                analysis += "Your glucose level is elevated. This may indicate prediabetes (100-125 mg/dL) "
                analysis += "or diabetes (126+ mg/dL) if consistently high. Elevated blood sugar can damage "
                analysis += "blood vessels and nerves over time if not addressed.\n\n"
                
                if glucose.get('value') and float(glucose.get('value', 0)) < 126:
                    analysis += "Your level suggests prediabetes, which means you're at increased risk for developing "
                    analysis += "diabetes but can often prevent or delay it through lifestyle changes.\n\n"
                else:
                    analysis += "Your level suggests possible diabetes. It's important to discuss these results "
                    analysis += "with your healthcare provider for proper diagnosis and treatment.\n\n"
            elif glucose.get('status') == "normal":
                analysis += "Your glucose level is within normal range, indicating healthy blood sugar control.\n\n"
            elif glucose.get('status') == "low":
                analysis += "Your glucose level is lower than normal. This could be due to various factors including "
                analysis += "medications, alcohol, not eating enough, or certain medical conditions. If you experience "
                analysis += "symptoms like shakiness, dizziness, or confusion, please consult your healthcare provider.\n\n"
        
        # Add A1C if available
        if a1c:
            analysis += f"HbA1c: {a1c.get('value', 'N/A')} {a1c.get('unit', '%')} "
            analysis += f"(Status: {a1c.get('status', 'unknown')})\n"
            analysis += f"Normal Range: {a1c.get('normalRange', '<5.7%')}\n\n"
            
            if a1c.get('status') == "elevated":
                analysis += "Your HbA1c is elevated. This reflects your average blood sugar over the past 2-3 months. "
                
                if a1c.get('value') and float(a1c.get('value', 0)) < 6.5:
                    analysis += "A level between 5.7-6.4% suggests prediabetes, indicating increased risk for developing diabetes.\n\n"
                else:
                    analysis += "A level of 6.5% or higher suggests diabetes. Please discuss these results with your healthcare provider.\n\n"
            elif a1c.get('status') == "normal":
                analysis += "Your HbA1c is within normal range, indicating good blood sugar control over the past 2-3 months.\n\n"
        
        # Add recommendations
        analysis += "General recommendations for blood sugar management:\n"
        analysis += "- Limit refined carbohydrates and added sugars\n"
        analysis += "- Choose complex carbohydrates with higher fiber content\n"
        analysis += "- Regular physical activity to improve insulin sensitivity\n"
        analysis += "- Maintain healthy weight\n"
        analysis += "- Stay hydrated\n"
        analysis += "- If prediabetic or diabetic, monitor blood sugar as recommended by your healthcare provider\n"
        
        return analysis
    
    def _analyze_vitamins(self, blood_tests: List[Dict[str, Any]]) -> str:
        """
        Analyze vitamin and mineral results to provide detailed insights.
        
        Args:
            blood_tests: List of blood test results
            
        Returns:
            str: Analysis of vitamin and mineral metrics
        """
        if not blood_tests or len(blood_tests) == 0:
            return "No blood test data available for vitamin and mineral analysis."
        
        # Get most recent blood test
        latest_test = blood_tests[0]
        results = latest_test.get("results", {})
        
        # Check for vitamin/mineral data
        vitamin_d = results.get("vitaminD", {})
        vitamin_b12 = results.get("vitaminB12", {})
        iron = results.get("iron", {})
        ferritin = results.get("ferritin", {})
        calcium = results.get("calcium", {})
        magnesium = results.get("magnesium", {})
        
        if not (vitamin_d or vitamin_b12 or iron or ferritin or calcium or magnesium):
            return "No vitamin or mineral data found in your blood test results."
        
        # Generate analysis
        analysis = f"Vitamin and Mineral Analysis (from {latest_test['date']}):\n\n"
        
        # Add Vitamin D
        if vitamin_d:
            analysis += f"Vitamin D: {vitamin_d.get('value', 'N/A')} {vitamin_d.get('unit', 'ng/mL')} "
            analysis += f"(Status: {vitamin_d.get('status', 'unknown')})\n"
            analysis += f"Normal Range: {vitamin_d.get('normalRange', '30-80 ng/mL')}\n\n"
            
            if vitamin_d.get('status') == "deficient":
                analysis += "You have vitamin D deficiency. Vitamin D is crucial for bone health, immune function, "
                analysis += "and mood regulation. Low levels are common, especially in people with limited sun exposure, "
                analysis += "darker skin, or certain dietary restrictions.\n\n"
                analysis += "Consider more sun exposure (15-30 minutes several times weekly), vitamin D-rich foods "
                analysis += "(fatty fish, fortified milk, egg yolks), and supplements as recommended by your doctor.\n\n"
            elif vitamin_d.get('status') == "insufficient":
                analysis += "Your vitamin D level is insufficient (suboptimal). Consider increasing sun exposure, "
                analysis += "consuming more vitamin D-rich foods, or supplements as recommended by your doctor.\n\n"
            elif vitamin_d.get('status') == "normal" or vitamin_d.get('status') == "optimal":
                analysis += "Your vitamin D level is adequate, which is good for bone health and immune function.\n\n"
        
        # Add other vitamins/minerals as needed
        
        return analysis
    
    # Backward compatibility method for the FastAPI app
    def process_message(self, message: str, health_data: Dict[str, Any], session_id: str) -> str:
        """
        Process a message from the user and generate a response using the health data.
        
        Args:
            message: User's message
            health_data: User's health data
            session_id: Session ID for tracking conversations
            
        Returns:
            str: Response to the user's message
        """
        # Store health data for the session
        self.sessions[session_id] = {
            "health_data": health_data
        }
        
        # Create message object
        msg = Message(
            role="user",
            content=message,
            sender="user",
            receiver=self.name,
            timestamp=datetime.now(),
            metadata={"health_data": health_data}
        )
        
        # Use the AI_Agent sender placeholder
        sender = AI_Agent("user", "user", "User of the health assistant")
        
        # Process using on_message
        response = self.on_message(msg, sender)
        
        # Return the text content
        return response.content 