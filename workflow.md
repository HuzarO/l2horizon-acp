## 📖 Development Workflow — Lineage Project

This document describes the workflow used in the project to organize development, releases and maintenance.

---

### 🚀 Main Branches

- **`main`**  
  Stable branch, where production-ready versions reside.  
  Receives merges only on releases.

- **`develop`**  
  Continuous development branch.  
  All development, new features and fixes should be done here.

---

### 🛠️ How to Work

#### 📌 1. Developing
Always make commits and pushes directly to `develop`:

```bash
git checkout develop
# edit files
git add .
git commit -m "Description of what was done"
git push
```

---

#### 📌 2. Creating a new release
When the project is ready for a new stable version:

```bash
git checkout main
git merge develop
git tag -a vX.X.X -m "Release description"
git push origin main --tags
```

- **vX.X.X** → follow the pattern `v1.0.1`, `v1.1.0`, etc.

---

#### 📌 3. Returning to development
After the release:

```bash
git checkout develop
```

And continue developing.

---

### ✅ Extra Tips

- Before starting anything:
  ```bash
  git pull
  ```
- Use clear and objective commit messages.
- Keep `main` clean, only with stable releases.
