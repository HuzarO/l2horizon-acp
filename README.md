# Definitive Lineage Panel [1.17](https://pdl.denky.dev.br)

<img align="right" height="180" src="https://i.imgur.com/0tL4OQ7.png"/>

PDL is a panel created with the mission to offer powerful tools for Lineage 2 private server administrators. Initially focused on risk analysis and server stability, the project has evolved and established itself as a complete solution for prospecting, management, and server operation — all in open source.

## Technologies Used

- **Python 3.14**: Modern and robust programming language used as the project base.
- **Django 5.2+**: Main web framework that allows rapid application development, with support for authentication, database management, and much more.
- **Gunicorn**: WSGI server to serve synchronous HTTP requests with high performance.
- **Daphne**: ASGI server to serve WebSockets and asynchronous requests.
- **Celery**: Library that allows execution of asynchronous background tasks, such as sending emails and data processing.
- **Redis**: In-memory data management system used as message broker for Celery, improving application performance.
- **Nginx**: Reverse web server that manages HTTP requests and serves static and media files.
- **Docker**: Used for application containerization, ensuring consistency and ease of deployment in different environments.
- **Docker Compose**: Tool that orchestrates multiple containers, facilitating service configuration and execution.

## Project Structure

### Services Defined in Docker Compose

- **site_http**: HTTP service that runs Django with Gunicorn (synchronous requests).
- **site_asgi**: ASGI service that runs Django with Daphne (WebSockets and asynchronous requests).
- **celery**: Celery worker that processes background tasks.
- **celery-beat**: Celery task scheduler that executes tasks at scheduled times.
- **flower**: Monitoring interface for Celery.
- **nginx**: Web server that acts as reverse proxy for Django services.
- **redis**: In-memory database used as message broker.
- **postgres**: PostgreSQL database for data storage.

### Volumes Used

- `logs`: To store application logs.
- `static`: To store application static files.
- `media`: To store media files uploaded by users.

### Network

- **lineage_network**: Network created to interconnect all services.

#

<p align="center">
<img height="280" src="https://i.imgur.com/gdB0k6o.jpeg">
</p>

[![Supported Python versions](https://img.shields.io/pypi/pyversions/Django.svg)](https://www.djangoproject.com/)


## ⚡ Quick Start

```bash
# Clone and install in 3 commands
git clone https://github.com/D3NKYT0/lineage.git
cd lineage
chmod +x install.sh && ./install.sh
```

Done! The `install.sh` script takes care of everything automatically. 🎉

**Note:** The project includes a `.gitattributes` that ensures consistent line endings. If you encounter issues with `git pull` detecting changes in `install.sh`, run:

```bash
# Normalize line endings (only once)
git add --renormalize .
git commit -m "Normalize line endings"
```

---

## 🚀 How to Install

### Quick Installation (Recommended)

PDL now has an automated installation script that facilitates the entire process:

```bash
# 1. Clone the repository
git clone https://github.com/D3NKYT0/lineage.git
cd lineage

# 2. Run the installation script
chmod +x install.sh
./install.sh
```

The `install.sh` script will:
- ✅ Automatically check prerequisites
- ✅ Install Docker and Docker Compose
- ✅ Configure Python environment
- ✅ Interactively generate `.env` file
- ✅ Build and start containers
- ✅ Apply database migrations

### 📋 install.sh Mini Tutorial

The `install.sh` is the central point for managing PDL. It offers several options:

#### Complete Installation (First Time)
```bash
./install.sh
# or
./install.sh install
```
Runs complete installation from scratch.

#### Interactive Menu
```bash
./install.sh menu
```
Opens a menu to choose which action to execute:
1. Complete installation
2. Setup only
3. Build only
4. Update repository (git pull)
5. Database backup
6. Configure reverse proxy
7. Install Nginx
8. Generate .env file
9. Configure FTP for launcher
10. Configure Nginx for launcher
11. List available scripts

#### Individual Commands

**Update the project:**
```bash
./install.sh update        # Updates repository and rebuilds (recommended)
# or
./install.sh build         # Rebuild only (after manual git pull)
```

**Make backup:**
```bash
./install.sh backup          # Create backup
./install.sh backup list     # List backups
./install.sh backup restore  # Restore backup
```

**Configure custom domain:**
```bash
./install.sh nginx-proxy
```

**Install/Update Nginx:**
```bash
./install.sh install-nginx        # Mainline version (default)
./install.sh install-nginx stable # Stable version
```

**Generate .env file:**
```bash
./install.sh generate-env
```

**Configure FTP for launcher:**
```bash
./install.sh setup-ftp
```

**Configure Nginx with index of for launcher:**
```bash
./install.sh setup-nginx-launcher
```

**Update repository:**
```bash
./install.sh update
```

**View help:**
```bash
./install.sh help
```

### 📝 Complete Installation Flow

1. **Clone the repository:**
   ```bash
   git clone https://github.com/D3NKYT0/lineage.git
   cd lineage
   ```

2. **Run installation:**
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

3. **Configure .env file:**
   - The script will generate `.env` interactively
   - You can choose which categories to include (Email, AWS S3, Payments, etc.)
   - Or edit manually later: `nano .env`

4. **Access the panel:**
   - URL: `http://localhost:6085`
   - Create your admin user when prompted

### 🔄 Update the Project

When a new version is released:

```bash
# Option 1: Use install.sh update command (recommended)
./install.sh update

# Option 2: Manually
git pull origin main
./install.sh build
```

**Tip:** If you're staff, the panel will automatically show when there's a new version available on GitHub!

### 📚 Complete Documentation

For more details about `install.sh`, see:
- [Complete install.sh Guide](docs/INSTALL_SH_GUIDE.md)


## 🔄 How to Update the Project

### Simple Update (Recommended)
```bash
cd /var/pdl/lineage  # or path where the project is
./install.sh update  # Updates repository and rebuilds automatically
```

### Manual Update
```bash
cd /var/pdl/lineage
git pull origin main
./install.sh build
```

### With Backup First
```bash
cd /var/pdl/lineage
./install.sh backup        # Make backup first
./install.sh update        # Update code and rebuild
```

## 💾 How to Backup the Database

### Manual Backup
```bash
cd /var/pdl/lineage
./install.sh backup
```

### Automatic Backup (Cron)
```bash
# Add to crontab for daily backup at 3am
crontab -e

# Add this line (using install.sh):
0 3 * * * cd /var/pdl/lineage && ./install.sh backup >> /var/pdl/backup.log 2>&1
```

### Other Backup Options
```bash
# List available backups
./install.sh backup list

# Restore backup
./install.sh backup restore
```

## 🔔 Update Checking

PDL has an automatic update checking system:

- **For Staff**: The panel automatically checks if there are new versions on GitHub
- **Visual Indicator**: 
  - 🟢 **Green** = Up to date version
  - 🟡 **Yellow** = New version available
- **Notification**: A button appears in the sidebar when an update is available
- **Instructions**: When clicked, a modal shows how to update step by step

### Check Manually
```bash
# Checking is automatic in the panel for staff
# But you can also check tags on GitHub:
curl https://api.github.com/repos/D3NKYT0/lineage/tags | grep '"name"'
```

## 🔧 Useful Commands

### Manage the Project (via install.sh)

**View all available scripts:**
```bash
./install.sh list
```

**View complete help:**
```bash
./install.sh help
```

**Interactive menu:**
```bash
./install.sh menu
```

### Manage Docker Containers

**Note:** For basic operations, use `install.sh`. For advanced operations, use direct commands:

```bash
# Start containers (after build)
docker compose up -d

# Stop containers
docker compose down

# View logs
docker compose logs -f

# Restart containers
docker compose restart

# Container status
docker compose ps
```

### Check Status
```bash
# Container status
docker compose ps

# Check current version
grep VERSION core/settings.py
```

### Available Scripts via install.sh

All scripts can be run through `install.sh`:

- `./install.sh install` - Complete installation
- `./install.sh setup` - Initial setup only
- `./install.sh build` - Build and deploy
- `./install.sh update` - Update repository and rebuild
- `./install.sh backup` - Database backup
- `./install.sh backup list` - List backups
- `./install.sh backup restore` - Restore backup
- `./install.sh nginx-proxy` - Configure reverse proxy
- `./install.sh install-nginx` - Install/update Nginx
- `./install.sh generate-env` - Generate .env file
- `./install.sh setup-ftp` - Configure FTP server for launcher
- `./install.sh setup-nginx-launcher` - Configure Nginx with index of for launcher
- `./install.sh list` - List all scripts
- `./install.sh help` - View complete help


## How to test (production)

```bash
https://pdl.denky.dev.br/
```

## About Me
>Developer - Daniel Amaral Recife/PE
- Emails: contato@denky.dev.br
- Discord: denkyto


## Staff Group:

**Programming Core**

- Daniel Amaral (Developer - FullStack/FullCycle)

**Support and Testers**

- Daniel Amaral (Developer - FullStack/FullCycle)

**Management**

- Daniel Amaral (Developer - FullStack/FullCycle)

## Code Structure

The project is coded using a simple and intuitive structure, shown below:

```bash
< PROJECT ROOT >
   |
   |-- apps/
   |    |
   |    |-- api/                             # REST API for external integrations
   |    |
   |    |-- main/
   |    |    |-- administrator/              # Administrative panel and settings
   |    |    |-- auditor/                    # Audit system and logs
   |    |    |-- calendary/                  # Event calendar and scheduling
   |    |    |-- downloads/                  # Download system (launcher, patches)
   |    |    |-- faq/                        # FAQ (Frequently Asked Questions)
   |    |    |-- home/                       # Main app - Dashboard and authentication
   |    |    |-- licence/                    # Licensing and activation system
   |    |    |-- management/                 # Django custom commands
   |    |    |-- message/                    # Message and friends system
   |    |    |-- news/                       # News and Blog
   |    |    |-- notification/               # Notification system (push, email, in-app)
   |    |    |-- resources/                  # Shared resources and utilities
   |    |    |-- social/                     # Integrated social network and moderation
   |    |    |-- solicitation/               # Requests and Support System
   |    |
   |    |-- lineage/
   |    |    |-- accountancy/                # Accounting and financial records
   |    |    |-- auction/                    # Auction system between players
   |    |    |-- games/                      # Minigames (roulette, boxes, dice, fishing)
   |    |    |-- inventory/                  # Inventory and items management
   |    |    |-- marketplace/                # Items marketplace between players
   |    |    |-- payment/                    # Payments (Mercado Pago, Stripe, PayPal)
   |    |    |-- reports/                    # Reports and administrative statistics
   |    |    |-- roadmap/                    # Public feature roadmap
   |    |    |-- server/                     # L2 server management and integration
   |    |    |-- shop/                       # Virtual store for items and services
   |    |    |-- tops/                       # Rankings (PvP, PK, Clan, Online)
   |    |    |-- wallet/                     # Virtual wallet and transactions
   |    |    |-- wiki/                       # Wiki for items, monsters and quests
   |    |
   |    |-- media_storage/                   # Media and file management
   |
   |-- core/
   |    |-- settings.py                      # Project settings
   |    |-- urls.py                          # Main routing
   |    |-- wsgi.py                          # WSGI server (Gunicorn)
   |    |-- asgi.py                          # ASGI server (Daphne)
   |    |-- celery.py                        # Celery configuration
   |    |-- *.py                             # Other configuration files
   |
   |-- requirements.txt                      # Project Python dependencies
   |-- docker-compose.yml                    # Container orchestration
   |-- Dockerfile                            # Application Docker image
   |-- manage.py                             # Django management script
   |-- gunicorn-cfg.py                       # Gunicorn configuration
   |-- ...                                   # Other files
   |
   |-- ************************************************************************
```

<br />

## How to Customize 

When a template file is loaded in the controller, `Django` scans all template directories, starting with user-defined ones, and returns the first found or an error if the template is not found. The theme used to style this initial project provides the following files:

```bash
< TEMPLATES AND THEMES STRUCTURE >

1. SYSTEM BASE TEMPLATES
   |-- templates/                            # Default PDL templates
   |    |-- admin/                           # Django Admin customizations (Jazzmin)
   |    |-- config/                          # Configuration pages
   |    |-- errors/                          # Error pages (400, 403, 404, 500)
   |    |-- includes/                        # Reusable components
   |    |    |-- head.html                   # Meta tags, favicon, CSS
   |    |    |-- nav.html                    # Main navigation
   |    |    |-- sidebar.html                # Sidebar menu (dashboard)
   |    |    |-- footer.html                 # Footer
   |    |    |-- scripts.html                # JavaScript scripts
   |    |    |-- floating-notifications.html # Floating notifications
   |    |    |-- analytics.html              # Analytics scripts
   |    |-- layouts/                         # Base layouts
   |    |    |-- base.html                   # Main layout (dashboard)
   |    |    |-- base-auth.html              # Authentication layout
   |    |    |-- base-default.html           # Default layout (landing page)
   |    |    |-- public.html                 # Public pages layout
   |    |-- public/                          # Public pages
   |    |    |-- index.html                  # Default landing page
   |    |    |-- downloads.html              # Downloads page
   |    |    |-- faq.html                    # Default FAQ
   |    |    |-- news_index.html             # News list
   |    |    |-- news_detail.html            # News details
   |    |    |-- privacy_policy.html         # Privacy policy
   |    |    |-- terms.html                  # Terms of service
   |    |    |-- user_agreement.html         # User agreement

2. CUSTOM THEMES SYSTEM
   |-- themes/                               # Installable themes system
   |    |-- installed/                       # Installed and active themes
   |    |    |
   |    |    |-- <theme-slug>/               # Theme directory (unique name)
   |    |    |    |
   |    |    |    |-- theme.json             # REQUIRED - Metadata and configuration
   |    |    |    |-- base.html              # REQUIRED - Theme base template
   |    |    |    |
   |    |    |    |-- index.html             # Customized landing page
   |    |    |    |-- news_index.html        # News list (theme)
   |    |    |    |-- news_detail.html       # News details (theme)
   |    |    |    |-- faq.html               # Customized FAQ
   |    |    |    |-- terms.html             # Terms of service (theme)
   |    |    |    |-- privacy_policy.html    # Privacy policy (theme)
   |    |    |    |-- user_agreement.html    # User agreement (theme)
   |    |    |    |-- *.html                 # Other customized templates
   |    |    |    |
   |    |    |    |-- css/                   # Theme styles
   |    |    |    |    |-- style.css         # Main styles
   |    |    |    |    |-- custom.css        # Additional customizations
   |    |    |    |    |-- responsive.css    # Responsive styles
   |    |    |    |    |-- *.css             # Other CSS files
   |    |    |    |
   |    |    |    |-- js/                    # Theme scripts
   |    |    |    |    |-- script.js         # Main scripts
   |    |    |    |    |-- custom.js         # Custom scripts
   |    |    |    |    |-- *.js              # Other scripts
   |    |    |    |
   |    |    |    |-- images/                # Images and visual assets
   |    |    |    |    |-- logo.png          # Server logo
   |    |    |    |    |-- favicon.png       # Site icon
   |    |    |    |    |-- bg/               # Background images
   |    |    |    |    |-- icons/            # Various icons
   |    |    |    |    |-- gallery/          # Screenshot gallery
   |    |    |    |    |-- characters/       # Character images
   |    |    |    |    |-- *.png, *.jpg      # Other images
   |    |    |    |
   |    |    |    |-- fonts/                 # Custom fonts (.woff, .ttf)
   |    |    |    |-- libs/                  # External JavaScript libraries
   |    |    |    |-- video/                 # Videos and trailers (.mp4, .webm)
   |    |    |    |-- assets/                # Other resources (optional)
   |    |    |
   |    |    |-- <other-theme>/              # Other installed themes
   |    |         |-- (same structure)

3. THEMES SYSTEM FUNCTIONALITY
   - Upload via Django Admin as ZIP file
   - Automatic validation of theme.json and structure
   - Extraction to /themes/installed/<slug>/
   - Only one active theme at a time
   - Internationalized variables (PT, EN, ES)
   - Automatic fallback to default templates
   - Hot-reload without restart needed

4. THEME VARIABLES (theme.json)
   - Support for multiple languages (value_pt, value_en, value_es)
   - Types: string, integer, boolean, color
   - Accessible in all templates via context processor
   - Customizable via admin panel

📚 Complete documentation: docs/THEME_SYSTEM.md, docs/GUIDE_CREATE_THEME.md
   
|-- ************************************************************************
```
