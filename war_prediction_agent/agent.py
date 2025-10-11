from typing import Dict, TypedDict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from models import AgentState, DataPoint, PredictionResponse, RiskLevel, RegionAnalysis, ConflictIndicator
from data_collectors import NewsCollector, MilitaryIntelCollector, SocialMediaCollector
from config import settings
import json
from datetime import datetime

class WarPredictionAgent:
    """LangGraph-based agent for war prediction"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=settings.TEMPERATURE,
            api_key=settings.OPENAI_API_KEY
        )
        self.news_collector = NewsCollector()
        self.military_collector = MilitaryIntelCollector()
        self.social_collector = SocialMediaCollector()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("collect_data", self._collect_data)
        workflow.add_node("analyze_relevance", self._analyze_relevance)
        workflow.add_node("extract_indicators", self._extract_indicators)
        workflow.add_node("calculate_risk", self._calculate_risk)
        workflow.add_node("generate_prediction", self._generate_prediction)
        
        # Add edges
        workflow.set_entry_point("collect_data")
        workflow.add_edge("collect_data", "analyze_relevance")
        workflow.add_edge("analyze_relevance", "extract_indicators")
        workflow.add_edge("extract_indicators", "calculate_risk")
        workflow.add_edge("calculate_risk", "generate_prediction")
        workflow.add_edge("generate_prediction", END)
        
        return workflow.compile()
    
    async def _collect_data(self, state: AgentState) -> Dict:
        """Collect data from all sources"""
        print("📡 Collecting data from sources...")
        
        try:
            news_data = await self.news_collector.collect()
            military_data = await self.military_collector.collect()
            social_data = await self.social_collector.collect()
            
            all_data = news_data + military_data + social_data
            
            return {
                "data_collected": all_data,
                "iteration": state.iteration + 1
            }
        except Exception as e:
            return {
                "errors": state.errors + [f"Data collection error: {str(e)}"]
            }
    
    async def _analyze_relevance(self, state: AgentState) -> Dict:
        """Analyze relevance and sentiment of collected data"""
        print("🔍 Analyzing data relevance...")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a military intelligence analyst. Analyze the following news items 
            and rate their relevance to potential war outbreak on a scale of 0-1.
            Also determine the sentiment (negative = -1, neutral = 0, positive = 1).
            
            Return JSON format:
            {{"relevance_score": float, "sentiment": float, "key_points": [str]}}"""),
            ("user", "Title: {title}\nContent: {content}")
        ])
        
        analyzed_data = []
        
        for item in state.data_collected[:50]:  # Analyze top 50 items
            try:
                response = await self.llm.ainvoke(
                    prompt.format_messages(title=item.title, content=item.content[:500])
                )
                
                analysis = json.loads(response.content)
                item.relevance_score = analysis.get("relevance_score", 0)
                item.sentiment = analysis.get("sentiment", 0)
                analyzed_data.append(item)
            except Exception as e:
                print(f"Analysis error: {e}")
                analyzed_data.append(item)
        
        # Sort by relevance
        analyzed_data.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return {
            "data_collected": analyzed_data,
            "analyzed_data": {"count": len(analyzed_data)}
        }
    
    async def _extract_indicators(self, state: AgentState) -> Dict:
        """Extract conflict indicators from data"""
        print("📊 Extracting conflict indicators...")
        
        # Get top relevant items
        top_items = [item for item in state.data_collected if item.relevance_score > 0.5]
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a conflict analysis expert. Based on the following data points,
            identify key conflict indicators and their severity.
            
            Consider:
            - Military mobilization
            - Diplomatic tensions
            - Border incidents
            - Weapons deployment
            - Alliance movements
            - Economic sanctions
            
            Return JSON:
            {{
                "indicators": [
                    {{"name": str, "severity": float (0-1), "region": str, "description": str}}
                ]
            }}"""),
            ("user", "Data points:\n{data}")
        ])
        
        data_summary = "\n\n".join([
            f"- {item.title} (Source: {item.source}, Score: {item.relevance_score})"
            for item in top_items[:20]
        ])
        
        try:
            response = await self.llm.ainvoke(prompt.format_messages(data=data_summary))
            indicators = json.loads(response.content)
            
            return {
                "analyzed_data": {
                    **state.analyzed_data,
                    "indicators": indicators.get("indicators", [])
                }
            }
        except Exception as e:
            return {
                "errors": state.errors + [f"Indicator extraction error: {str(e)}"]
            }
    
    async def _calculate_risk(self, state: AgentState) -> Dict:
        """Calculate risk scores by region"""
        print("⚠️  Calculating risk scores...")
        
        indicators = state.analyzed_data.get("indicators", [])
        
        # Group by region
        regional_risks = {}
        for indicator in indicators:
            region = indicator.get("region", "Global")
            severity = indicator.get("severity", 0)
            
            if region not in regional_risks:
                regional_risks[region] = []
            regional_risks[region].append(severity)
        
        # Calculate average risk per region
        risk_scores = {
            region: sum(scores) / len(scores) if scores else 0
            for region, scores in regional_risks.items()
        }
        
        return {
            "risk_scores": risk_scores,
            "analyzed_data": {
                **state.analyzed_data,
                "regional_risks": regional_risks
            }
        }
    
    async def _generate_prediction(self, state: AgentState) -> Dict:
        """Generate final prediction with reasoning"""
        print("🎯 Generating prediction...")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a geopolitical expert providing war risk assessment.
            
            Based on the analyzed data and risk scores, provide:
            1. Global risk assessment (0-1 scale)
            2. Regional breakdowns
            3. Key events driving the risk
            4. Confidence level
            5. Detailed reasoning
            
            Be objective and evidence-based."""),
            ("user", """Risk Scores: {risk_scores}
            
            Indicators: {indicators}
            
            Top Events: {top_events}
            
            Provide comprehensive analysis.""")
        ])
        
        top_events = [
            {"title": item.title, "source": item.source, "score": item.relevance_score}
            for item in state.data_collected[:10]
        ]
        
        try:
            response = await self.llm.ainvoke(prompt.format_messages(
                risk_scores=json.dumps(state.risk_scores),
                indicators=json.dumps(state.analyzed_data.get("indicators", [])),
                top_events=json.dumps(top_events)
            ))
            
            # Calculate global risk
            global_risk = sum(state.risk_scores.values()) / len(state.risk_scores) if state.risk_scores else 0
            
            # Determine risk level
            if global_risk < settings.LOW_RISK_THRESHOLD:
                risk_level = RiskLevel.LOW
            elif global_risk < settings.MEDIUM_RISK_THRESHOLD:
                risk_level = RiskLevel.MEDIUM
            elif global_risk < settings.HIGH_RISK_THRESHOLD:
                risk_level = RiskLevel.HIGH
            else:
                risk_level = RiskLevel.CRITICAL
            
            # Build regional analyses
            regional_analyses = []
            for region, score in state.risk_scores.items():
                region_level = RiskLevel.LOW
                if score >= settings.HIGH_RISK_THRESHOLD:
                    region_level = RiskLevel.CRITICAL
                elif score >= settings.MEDIUM_RISK_THRESHOLD:
                    region_level = RiskLevel.HIGH
                elif score >= settings.LOW_RISK_THRESHOLD:
                    region_level = RiskLevel.MEDIUM
                
                regional_analyses.append(RegionAnalysis(
                    region=region,
                    risk_score=score,
                    risk_level=region_level,
                    indicators=[],
                    active_conflicts=[],
                    data_points_analyzed=len(state.data_collected)
                ))
            
            prediction = PredictionResponse(
                timestamp=datetime.now(),
                global_risk_score=global_risk,
                global_risk_level=risk_level,
                regional_analyses=regional_analyses,
                key_events=state.data_collected[:10],
                confidence=0.75,
                reasoning=response.content,
                sources_analyzed=len(state.data_collected)
            )
            
            return {"final_prediction": prediction}
            
        except Exception as e:
            return {
                "errors": state.errors + [f"Prediction generation error: {str(e)}"]
            }
    
    async def predict(self, hours_back: int = 24) -> PredictionResponse:
        """Run the full prediction pipeline"""
        initial_state = AgentState()
        
        result = await self.graph.ainvoke(initial_state)
        
        if result.get("final_prediction"):
            return result["final_prediction"]
        else:
            raise Exception(f"Prediction failed: {result.get('errors')}")