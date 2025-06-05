#!/bin/bash
echo "🚀 Setting up SQL RAG Translator environment..."

# Detect shell configuration file
if [ -f ~/.bashrc ]; then
    SHELL_CONFIG=~/.bashrc
elif [ -f ~/.bash_profile ]; then
    SHELL_CONFIG=~/.bash_profile
else
    # Create .bash_profile if neither exists
    touch ~/.bash_profile
    SHELL_CONFIG=~/.bash_profile
fi

echo "Using shell config file: $SHELL_CONFIG"

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH for current session
    eval "$(/opt/homebrew/bin/brew shellenv)"
    
    # Add Homebrew to shell config
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> $SHELL_CONFIG
fi

# Install PostgreSQL 16
echo "📦 Installing PostgreSQL 16..."
brew install postgresql@16
brew services start postgresql@16

# Add PostgreSQL to PATH
echo 'export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"' >> $SHELL_CONFIG

# Install MySQL 8.0
echo "📦 Installing MySQL 8.0..."
brew install mysql
brew services start mysql

# Install Docker
echo "📦 Installing Docker..."
brew install --cask docker

echo "✅ Environment setup complete!"
echo "🔄 Please run: source $SHELL_CONFIG"
echo "📝 Then test with: which psql"
echo "🗄️  Create database with: createdb banking_rag_db"
