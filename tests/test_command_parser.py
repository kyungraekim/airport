import pytest
from app.utils.command_parser import CommandParser
from app.models.commands import CommandType

def test_parse_train_command():
    """Test parsing train command."""
    command = "/train --config=new --epochs=10 --lr=0.001"
    config = CommandParser.parse_command(command)
    
    assert config is not None
    assert config.command_type == CommandType.TRAIN
    assert config.raw_command == command
    assert config.config == "new"
    assert config.epochs == 10
    assert config.learning_rate == 0.001

def test_parse_eval_command():
    """Test parsing eval command.""" 
    command = "/eval --model=baseline,incoming --metrics=accuracy,f1"
    config = CommandParser.parse_command(command)
    
    assert config is not None
    assert config.command_type == CommandType.EVAL
    assert config.model == ["baseline", "incoming"]
    assert config.metrics == ["accuracy", "f1"]

def test_parse_help_command():
    """Test parsing help command."""
    command = "/help"
    config = CommandParser.parse_command(command)
    
    assert config is not None
    assert config.command_type == CommandType.HELP

def test_parse_invalid_command():
    """Test parsing invalid command."""
    command = "/invalid_command"
    config = CommandParser.parse_command(command)
    
    assert config is None

def test_parse_command_without_slash():
    """Test parsing command without slash prefix."""
    command = "train --epochs=5"
    config = CommandParser.parse_command(command)
    
    assert config is None

def test_get_help_text():
    """Test help text generation."""
    help_text = CommandParser.get_help_text()
    assert "Available Commands" in help_text
    assert "/train" in help_text
    assert "/eval" in help_text
    
    train_help = CommandParser.get_help_text(CommandType.TRAIN)
    assert "Train Command Usage" in train_help
    assert "--epochs" in train_help