import os
import logging
from typing import Dict, Any, List, Optional
from pinai_agent_sdk import PINAIAgentSDK, AGENT_CATEGORY_DAILY
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class HealthAIAgent:
    """
    Health AI Agent using the PinAI SDK to provide health insights and recommendations
    based on user's personal health data.
    """
    
    def __init__(self):
        """Initialize the Health AI Agent with PinAI SDK."""
        # Get API key from environment variable
        self.api_key = os.getenv("PINAI_API_KEY", "")
        self.agent_id = os.getenv("PINAI_AGENT_ID", None)
        
        if not self.api_key:
            logger.warning("PINAI_API_KEY environment variable not set. Some features may not work.")
        
        # Initialize the PinAI SDK client
        self.sdk_client = self._initialize_sdk_client()
        
        # Register agent if no agent_id is available
        if not self.agent_id:
            self._register_agent()
        
        # Store sessions and health data mapping
        self.sessions = {}
    
    def _initialize_sdk_client(self) -> PINAIAgentSDK:
        """Initialize the PinAI SDK client."""
        try:
            return PINAIAgentSDK(api_key=self.api_key)
        except Exception as e:
            logger.error(f"Failed to initialize PinAI SDK client: {e}")
            # Create a dummy client for development if API key is missing
            return None
    
    def _register_agent(self) -> None:
        """Register the Health AI Agent with PinAI platform."""
        if not self.sdk_client:
            logger.error("Cannot register agent: SDK client not initialized")
            return
        
        try:
            agent_info = self.sdk_client.register_agent(
                name="Health AI Assistant",
                description="Personal health assistant that analyzes your health data and provides insights and recommendations",
                category=AGENT_CATEGORY_DAILY,
            )
            
            self.agent_id = agent_info.get("id")
            logger.info(f"Registered Health AI Agent with ID: {self.agent_id}")
            
            # Save agent_id for future use
            os.environ["PINAI_AGENT_ID"] = str(self.agent_id)
        except Exception as e:
            logger.error(f"Failed to register agent: {e}")
    
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
        
        # Check message intent and generate appropriate response
        message_lower = message.lower()
        
        # Check if message is about blood tests
        if "blood test" in message_lower or "blood work" in message_lower:
            return self._analyze_blood_test(health_data.get("bloodTests", []))
        
        # Check if message is about vital signs
        elif "vital" in message_lower or "blood pressure" in message_lower:
            return self._analyze_vitals(health_data.get("vitals", []))
        
        # Check if message is asking for recommendations
        elif "recommend" in message_lower or "advice" in message_lower or "suggestion" in message_lower:
            return self._generate_health_recommendations(health_data)
        
        # Check if message is about overall health status
        elif "health status" in message_lower or "health overview" in message_lower or "my health" in message_lower:
            blood_analysis = self._analyze_blood_test(health_data.get("bloodTests", []))
            vitals_analysis = self._analyze_vitals(health_data.get("vitals", []))
            return f"Health Overview:\n\n{blood_analysis}\n\n{vitals_analysis}"
        
        # If we have the PinAI SDK client, try to use it for other messages
        elif self.sdk_client and self.agent_id:
            try:
                # Convert health data to a format usable by the agent
                health_context = json.dumps(health_data)
                
                # Use the PinAI SDK to generate a response (actual implementation would depend on API details)
                def handle_message(agent_message):
                    # Process the incoming message from the agent
                    return f"Based on your health data: {agent_message['content']}"
                
                # Start the agent (non-blocking to avoid hanging)
                self.sdk_client.start(
                    on_message_callback=handle_message,
                    agent_id=self.agent_id
                )
                
                # Send message to agent
                response = self.sdk_client.send_message(
                    content=message,
                    session_id=session_id,
                    meta_data={"health_data": health_context}
                )
                
                # If we couldn't get a response from the agent, use fallback
                if not response:
                    return "I'm your Health AI Assistant. I can help analyze your blood tests, vital signs, and provide health recommendations. What would you like to know about your health?"
                
                return response
            except Exception as e:
                logger.error(f"Error using PinAI SDK: {e}")
                # Fall back to default response
                return "I'm your Health AI Assistant. I can help analyze your blood tests, vital signs, and provide health recommendations. What would you like to know about your health?"
        
        # Default response
        else:
            return "I'm your Health AI Assistant. I can help analyze your blood tests, vital signs, and provide health recommendations. What would you like to know about your health?" 