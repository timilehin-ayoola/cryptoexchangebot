# Contributing to Nigerian P2P Crypto Exchange Bot

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Report security issues privately (don't open public issues)

## Getting Started

### 1. Fork & Clone

```bash
git clone https://github.com/yourusername/crypto_exchange_bot.git
cd crypto_exchange_bot
```

### 2. Setup Development Environment

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

## Development Guidelines

### Code Style

- **Follow PEP 8**: Use `black` for formatting
  ```bash
  pip install black
  black .
  ```

- **Type Hints**: All functions must have type annotations
  ```python
  def get_user(user_id: int) -> Optional[Dict[str, Any]]:
      """Retrieve user profile."""
      pass
  ```

- **Docstrings**: Use Google-style docstrings
  ```python
  def my_function(param: str) -> bool:
      """Brief description.
      
      Longer description if needed.
      
      Args:
          param: Parameter description.
          
      Returns:
          bool: Description of return value.
          
      Raises:
          ValueError: When something goes wrong.
      """
      pass
  ```

- **Logging**: Use logger for all messages
  ```python
  logger.info("User action completed")
  logger.error(f"Failed to process: {e}")
  ```

### Commit Messages

Follow conventional commits format:

```
type(scope): description

[optional body]

[optional footer]
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Examples**:
- `feat(buy): Add double-confirmation for wallet address`
- `fix(database): Handle connection timeout gracefully`
- `docs(readme): Update deployment instructions`

### File Organization

```
crypto_exchange_bot/
├── bot.py              # Main logic (keep ~1500 lines max)
├── config.py           # Configuration only
├── database.py         # Database operations
├── responses.py        # Response templates
└── utils/
    ├── bank_utils.py
    └── tron_utils.py
```

### Testing

1. **Manual Testing**: Test in Telegram first
   - Create a test bot with BotFather
   - Use `.env.test` for development credentials

2. **Error Scenarios**: Test edge cases
   - Invalid input formats
   - Network failures
   - Missing credentials

3. **Security**: Never commit
   - `.env` files
   - Private keys
   - Real credentials

## Pull Request Process

### Before Submitting

1. **Check existing issues/PRs**: Avoid duplicates
2. **Update code**: Follow code style guidelines
3. **Test thoroughly**: Manual test in Telegram
4. **Update documentation**: README, docstrings, comments
5. **Keep commits clean**: One feature per commit

### Submitting PR

1. Push to your fork
2. Create PR with descriptive title and description
3. Link related issues using `Closes #123`
4. Fill out PR template:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe testing performed:
- Tested in Telegram with...
- Edge cases covered: ...

## Screenshots
If UI changes, add screenshots

## Checklist
- [ ] Code follows style guidelines
- [ ] Added/updated docstrings
- [ ] Added/updated type hints
- [ ] Tested edge cases
- [ ] Updated README if needed
- [ ] No secrets committed
```

## Feature Development

### Adding a New Feature

1. **Plan it out**
   ```python
   # bot.py
   async def new_feature(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
       """Brief description."""
       # Implementation
   ```

2. **Add documentation**
   ```python
   async def new_feature(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
       """
       Feature description.
       
       This feature does X, Y, and Z. It integrates with:
       - Database module for persistence
       - TronGrid for blockchain verification
       
       Args:
           update: Telegram update object
           context: Handler context with user data
       """
   ```

3. **Add error handling**
   ```python
   try:
       # Feature logic
   except ValueError as e:
       logger.error(f"Feature Error: Invalid input: {e}")
       await update.message.reply_text(get_text("ERROR_MESSAGE"))
   except Exception as e:
       logger.error(f"Feature Error: Unexpected error: {e}")
       await update.message.reply_text(get_text("ERROR_GENERIC"))
   ```

4. **Add response variations** (if user-facing)
   ```python
   # responses.py
   "FEATURE_START": [
       "Option 1 response variation",
       "Option 2 response variation",
       "Option 3 response variation",
   ]
   ```

5. **Register handler**
   ```python
   # bot.py main()
   app.add_handler(CommandHandler("newfeature", new_feature))
   app.add_handler(MessageHandler(filters.Regex(r'(?i)^newfeature'), new_feature))
   ```

### Bug Fixes

1. **Reproduce the bug**: Provide steps to reproduce
2. **Fix the code**: Make minimal changes
3. **Add logging**: For debugging
4. **Test thoroughly**: Ensure fix works and doesn't break other features

## Documentation

### Updating Documentation

- **README**: For user-facing info, setup instructions
- **Code Comments**: For complex logic explaining the "why"
- **Docstrings**: For function signatures and behavior
- **Commit Messages**: For historical context

### Documentation Standards

- Keep it clear and concise
- Use active voice ("The bot handles" not "Should be handled")
- Include examples for complex features
- Update all related docs if making changes

## Reporting Issues

### Bug Reports

Include:
- **Description**: What went wrong?
- **Steps to reproduce**: How to trigger the bug
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happened
- **Environment**: Python version, hosting platform, etc.
- **Logs**: Error messages, stack traces

### Feature Requests

Include:
- **Use case**: Why is this needed?
- **Description**: What should it do?
- **Examples**: How would users interact with it?
- **Impact**: How many users would benefit?

## Security

### Reporting Security Issues

**DO NOT** open public issues for security vulnerabilities.

Instead, email: [your-email@example.com](mailto:your-email@example.com)

Include:
- Vulnerability description
- Steps to reproduce
- Potential impact
- Suggested fix (if known)

## Recognition

Contributors will be recognized in:
- README contributors section
- Release notes
- Commit history (forever!)

## Questions?

- Open a discussion on GitHub
- Contact maintainers directly
- Check existing documentation

---

**Thank you for making this bot better! 🙏**
