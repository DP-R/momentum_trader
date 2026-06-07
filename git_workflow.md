# Standard Git Workflow

Here are the standard commands you will use to commit and push changes to your GitHub repository:

1. **Check the status of your files** (see what has changed):
   ```bash
   git status
   ```

2. **Stage your changes** (prepare them to be committed):
   To stage a specific file:
   ```bash
   git add <filename>
   ```
   To stage *all* modified and new files:
   ```bash
   git add .
   ```

3. **Commit your changes** (save them locally with a message):
   ```bash
   git commit -m "Write a brief description of your changes here"
   ```

4. **Push your changes** (upload them to GitHub):
   ```bash
   git push
   ```

### Example usage:
```bash
git status
git add main.py
git commit -m "Update main.py to fix data extraction bug"
git push
```
