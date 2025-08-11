import re
import shlex
from typing import Dict, Any, Optional, List
import structlog

from app.models.commands import CommandConfig, CommandType

logger = structlog.get_logger()

class CommandParser:
    """Parser for slash commands with flexible argument handling."""
    
    @staticmethod
    def parse_command(command_text: str) -> Optional[CommandConfig]:
        """Parse a slash command string into a CommandConfig object."""
        try:
            command_text = command_text.strip()
            if not command_text.startswith('/'):
                return None
            
            # Remove leading slash and split into tokens
            tokens = shlex.split(command_text[1:])  # Remove '/' and split properly
            if not tokens:
                return None
            
            command_name = tokens[0].lower()
            
            # Validate command type
            try:
                command_type = CommandType(command_name)
            except ValueError:
                logger.error(f"Unknown command type: {command_name}")
                return None
            
            # Parse arguments
            args = CommandParser._parse_arguments(tokens[1:])
            
            # Create CommandConfig with parsed arguments
            config_data = {
                'command_type': command_type,
                'raw_command': command_text,
                'arguments': args,
            }
            
            # Map common arguments to specific fields
            config_data.update(CommandParser._map_arguments(args, command_type))
            
            return CommandConfig(**config_data)
            
        except Exception as e:
            logger.error(f"Error parsing command: {e}", command_text=command_text)
            return None
    
    @staticmethod
    def _parse_arguments(arg_tokens: List[str]) -> Dict[str, Any]:
        """Parse command arguments into key-value pairs."""
        args = {}
        i = 0
        
        while i < len(arg_tokens):
            token = arg_tokens[i]
            
            if token.startswith('--'):
                # Long argument format: --key=value or --key value
                if '=' in token:
                    key, value = token[2:].split('=', 1)
                    args[key] = CommandParser._parse_value(value)
                else:
                    # Look for value in next token
                    key = token[2:]
                    if i + 1 < len(arg_tokens) and not arg_tokens[i + 1].startswith('-'):
                        i += 1
                        args[key] = CommandParser._parse_value(arg_tokens[i])
                    else:
                        # Boolean flag
                        args[key] = True
            
            elif token.startswith('-') and len(token) == 2:
                # Short argument format: -k value or -k
                key = CommandParser._expand_short_arg(token[1])
                if i + 1 < len(arg_tokens) and not arg_tokens[i + 1].startswith('-'):
                    i += 1
                    args[key] = CommandParser._parse_value(arg_tokens[i])
                else:
                    # Boolean flag
                    args[key] = True
            
            else:
                # Positional argument (treat as a flag for now)
                args[token] = True
            
            i += 1
        
        return args
    
    @staticmethod
    def _expand_short_arg(short_arg: str) -> str:
        """Expand short argument to full name."""
        short_to_long = {
            'e': 'epochs',
            'l': 'lr',
            'g': 'gpu',
            'b': 'batch_size',
            'c': 'config',
            'm': 'model',
            't': 'type',
            's': 'samples',
            'j': 'job_id',
        }
        return short_to_long.get(short_arg, short_arg)
    
    @staticmethod
    def _parse_value(value: str) -> Any:
        """Parse string value to appropriate type."""
        # Try to parse as number
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # Try to parse as boolean
        if value.lower() in ('true', 'yes', 'on', '1'):
            return True
        elif value.lower() in ('false', 'no', 'off', '0'):
            return False
        
        # Return as string
        return value
    
    @staticmethod
    def _map_arguments(args: Dict[str, Any], command_type: CommandType) -> Dict[str, Any]:
        """Map parsed arguments to CommandConfig fields based on command type."""
        mapped = {}
        
        # Common arguments
        for key in ['config', 'epochs', 'lr', 'gpu', 'batch_size']:
            if key in args:
                mapped[key] = args[key]
        
        # Command-specific arguments
        if command_type == CommandType.EVAL:
            if 'model' in args:
                mapped['model'] = CommandParser._parse_list_arg(args['model'])
            if 'metrics' in args:
                mapped['metrics'] = CommandParser._parse_list_arg(args['metrics'])
        
        elif command_type == CommandType.TEST:
            if 'type' in args:
                mapped['test_type'] = args['type']
            if 'samples' in args:
                mapped['samples'] = args['samples']
        
        elif command_type == CommandType.PIPELINE:
            if 'steps' in args:
                mapped['steps'] = CommandParser._parse_list_arg(args['steps'])
            if 'skip' in args:
                mapped['skip'] = CommandParser._parse_list_arg(args['skip'])
        
        elif command_type == CommandType.STATUS:
            if 'job' in args or 'job_id' in args:
                mapped['job_id'] = args.get('job', args.get('job_id'))
        
        return mapped
    
    @staticmethod
    def _parse_list_arg(value: Any) -> List[str]:
        """Parse comma-separated string into list."""
        if isinstance(value, str):
            return [item.strip() for item in value.split(',') if item.strip()]
        elif isinstance(value, list):
            return value
        else:
            return [str(value)]

    @staticmethod
    def get_help_text(command_type: Optional[CommandType] = None) -> str:
        """Get help text for commands."""
        if command_type == CommandType.TRAIN:
            return """
**Train Command Usage:**
`/train --config=<config> --epochs=<n> --lr=<rate> --gpu=<count>`

Examples:
- `/train --config=new --epochs=10 --lr=0.001`
- `/train --epochs=50 --gpu=2 --batch_size=32`
            """.strip()
        
        elif command_type == CommandType.EVAL:
            return """
**Eval Command Usage:**
`/eval --model=<models> --metrics=<metrics>`

Examples:
- `/eval --model=baseline,incoming --metrics=accuracy,f1`
- `/eval --model=latest --metrics=all`
            """.strip()
        
        elif command_type == CommandType.TEST:
            return """
**Test Command Usage:**
`/test --type=<test_type> --samples=<n>`

Examples:
- `/test --type=smoke --samples=100`
- `/test --type=integration`
            """.strip()
        
        elif command_type == CommandType.PIPELINE:
            return """
**Pipeline Command Usage:**
`/pipeline --steps=<steps> --skip=<steps>`

Examples:
- `/pipeline --steps=train,eval --skip=test`
- `/pipeline --steps=all`
            """.strip()
        
        elif command_type == CommandType.STATUS:
            return """
**Status Command Usage:**
`/status --job=<job_id>`

Examples:
- `/status --job=abc123`
- `/status` (shows all active jobs)
            """.strip()
        
        else:
            return """
**Available Commands:**

**🔬 Issue Commands (Long-running ML jobs):**
- `/train` - Train a model with specified parameters  
- `/eval` - Evaluate models with metrics
- `/pipeline` - Execute a multi-step pipeline

**🧪 Pull Request Commands (Testing changes):**
- `/test` - Run tests on models

**📊 Universal Commands (Work anywhere):**
- `/status` - Check job status
- `/help` - Show this help message

**💡 Hybrid Approach:**
- **Issues**: For planning, ML experiments, and long-running jobs
- **Pull Requests**: For testing specific code changes  
- **Both**: Status updates and help

Use `/help <command>` for detailed command usage.
            """.strip()