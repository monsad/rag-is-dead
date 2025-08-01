#!/usr/bin/env python3
"""
🚀 SQL Agent API - Deployment Helper Script
Choose and test your deployment option
"""

import os
import subprocess
import sys

def print_header():
    print("=" * 80)
    print("🚀 SQL AGENT API - DEPLOYMENT HELPER")
    print("=" * 80)
    print("Choose your deployment platform:")
    print()

def print_options():
    print("1. 🥇 Railway (RECOMMENDED - Free + Easy)")
    print("   • Free $5/month credit")
    print("   • Automatic GitHub deployment") 
    print("   • Zero configuration needed")
    print()
    
    print("2. 🥈 Render (Great Free Option)")
    print("   • Generous free tier")
    print("   • Easy setup")
    print("   • Automatic HTTPS")
    print()
    
    print("3. 🥉 Heroku (Classic PaaS)")
    print("   • Most popular platform")
    print("   • No free tier ($7/month)")
    print("   • Extensive documentation")
    print()
    
    print("4. 🔥 AWS Lambda (Serverless)")
    print("   • Pay per request")
    print("   • Infinite scaling")
    print("   • More complex setup")
    print()
    
    print("5. 🧪 Test Local Deployment")
    print("   • Test your production config locally")
    print()
    
    print("6. 📋 Show Environment Variables")
    print("   • Display required env vars")
    print()

def test_local():
    """Test the production-ready API locally"""
    print("🧪 Testing local deployment...")
    print("Starting production server on http://localhost:8000")
    print("Press Ctrl+C to stop")
    print()
    
    try:
        subprocess.run([
            "python", "main.py"
        ], check=True)
    except KeyboardInterrupt:
        print("\n✅ Local test completed!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")

def show_env_vars():
    """Show required environment variables"""
    print("📋 REQUIRED ENVIRONMENT VARIABLES:")
    print("=" * 50)
    print()
    print("# Database Configuration")
    print("DB_HOST=your_postgres_host")
    print("DB_PORT=5432")
    print("DB_NAME=your_database_name") 
    print("DB_USER=your_username")
    print("DB_PASSWORD=your_password")
    print()
    print("# OpenAI Configuration")
    print("OPENAI_API_KEY=your_openai_api_key_here")
    print()
    print("# Optional")
    print("PORT=8000")
    print("HOST=0.0.0.0")
    print()
    print("💡 Copy these to your .env file or deployment platform!")

def railway_instructions():
    print("🥇 RAILWAY DEPLOYMENT INSTRUCTIONS:")
    print("=" * 50)
    print()
    print("1. 📁 Push your code to GitHub:")
    print("   git add .")
    print("   git commit -m 'Ready for Railway deployment'")
    print("   git push origin main")
    print()
    print("2. 🌐 Go to https://railway.app")
    print("3. 🔗 Click 'Start a New Project'")
    print("4. 📂 Connect your GitHub repository")
    print("5. 🚀 Railway will auto-deploy your FastAPI!")
    print()
    print("6. ⚙️  Set Environment Variables in Railway dashboard:")
    show_env_vars()
    print()
    print("🎉 Your API will be live at: https://your-app-name.up.railway.app")

def render_instructions():
    print("🥈 RENDER DEPLOYMENT INSTRUCTIONS:")
    print("=" * 50)
    print()
    print("1. 🌐 Go to https://render.com")
    print("2. 🔗 Connect your GitHub repository")
    print("3. 📝 Create new Web Service with:")
    print("   • Build Command: pip install -r requirements.txt")
    print("   • Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT")
    print("4. ⚙️  Add Environment Variables:")
    show_env_vars()
    print()
    print("🎉 Your API will be live at: https://your-app-name.onrender.com")

def heroku_instructions():
    print("🥉 HEROKU DEPLOYMENT INSTRUCTIONS:")
    print("=" * 50)
    print()
    print("1. 📦 Install Heroku CLI:")
    print("   brew install heroku/brew/heroku")
    print()
    print("2. 🔐 Login and create app:")
    print("   heroku login")
    print("   heroku create your-sql-agent-api")
    print()
    print("3. ⚙️  Set environment variables:")
    print("   heroku config:set DB_HOST=your_postgres_host")
    print("   heroku config:set DB_PORT=5432")
    print("   heroku config:set DB_NAME=your_database_name")
    print("   heroku config:set DB_USER=your_username")
    print("   heroku config:set DB_PASSWORD=your_password") 
    print("   heroku config:set OPENAI_API_KEY=your_openai_api_key")
    print()
    print("4. 🚀 Deploy:")
    print("   git push heroku main")
    print()
    print("🎉 Your API will be live at: https://your-sql-agent-api.herokuapp.com")

def lambda_instructions():
    print("🔥 AWS LAMBDA DEPLOYMENT INSTRUCTIONS:")
    print("=" * 50)
    print()
    print("⚠️  This is the most advanced option!")
    print()
    print("1. 📦 Install AWS CLI and SAM:")
    print("   brew install aws-cli aws-sam-cli")
    print("   aws configure")
    print()
    print("2. 📄 Your lambda_handler.py is ready!")
    print("3. 📋 See DEPLOYMENT_GUIDE.md for complete SAM template")
    print("4. 🚀 Deploy with:")
    print("   sam build")
    print("   sam deploy --guided")
    print()
    print("🎉 Your API will be live at: https://your-api-id.execute-api.region.amazonaws.com/Prod")

def main():
    print_header()
    print_options()
    print("=" * 80)
    
    try:
        choice = input("Enter your choice (1-6): ").strip()
        print()
        
        if choice == "1":
            railway_instructions()
        elif choice == "2":
            render_instructions()
        elif choice == "3":
            heroku_instructions() 
        elif choice == "4":
            lambda_instructions()
        elif choice == "5":
            test_local()
        elif choice == "6":
            show_env_vars()
        else:
            print("❌ Invalid choice. Please run again and choose 1-6.")
            return
            
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        return

    print("\n" + "=" * 80)
    print("📚 For detailed instructions, see: DEPLOYMENT_GUIDE.md")
    print("🆘 Need help? Check the deployment logs on your chosen platform")
    print("=" * 80)

if __name__ == "__main__":
    main()