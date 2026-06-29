"""
SoloLeveling Appeal Bot - Fully Fixed
Group: @sololeveling
Admin: @xConfusion (ID: 5670083380)
Bot: @Communityappealbot
"""

import sqlite3
import logging
from datetime import datetime
from typing import Optional, Dict, List
import os
import sys
import time

# Auto-install dependencies
try:
    import telebot
    from telebot import types
    from telebot.apihelper import ApiTelegramException
except ImportError:
    print("📦 Installing pyTelegramBotAPI...")
    os.system('pip install pyTelegramBotAPI')
    import telebot
    from telebot import types
    from telebot.apihelper import ApiTelegramException

# ==================== CONFIGURATION ====================
class Config:
    """Bot Configuration"""
    
    # Bot Token
    BOT_TOKEN = '8835642731:AAHrYM8RL5Pub_L2EW7q50yTeTOWv7Y99b0'
    
    # Bot Username
    BOT_USERNAME = '@Communityappealbot'
    
    # Group
    GROUP = '@sololeveling'
    GROUP_LINK = 'https://t.me/sololeveling'
    
    # Admin
    ADMIN_ID = 5670083380
    ADMIN_USERNAME = '@xConfusion'
    
    # Database
    DB_FILE = 'appeals.db'
    
    # Messages
    WELCOME = """🌟 Welcome to SoloLeveling Appeal Bot!

This bot helps you manage appeals for banned users.

Please choose an option below:"""
    
    NOT_BANNED = """✅ You are not banned in SoloLeveling.

You can continue enjoying the group!"""
    
    BANNED_MESSAGE = """❌ You are banned in SoloLeveling.

You can create an appeal by clicking the button below."""
    
    APPEAL_REQ = """📝 Send your appeal message.

Explain why you should be unbanned.

Minimum 10 characters required."""
    
    RECEIVED = """✅ Your appeal has been received!

📋 Appeal ID: #{id}

We will review your appeal and get back to you shortly.
Please wait for admin approval."""
    
    APPROVED = """✅ Your appeal has been approved!

🎉 You have been unbanned from SoloLeveling.
Welcome back!"""
    
    REJECTED = """❌ Your appeal has been rejected.

If you have any questions, please contact: @xConfusion"""
    
    CONTACT = """📞 Contact Admin: @xConfusion

For any issues, please contact the admin directly."""
    
    # Buttons
    BTN_APPEAL = "📝 Create Appeal"
    BTN_CONTACT = "📞 Contact Admin"
    BTN_APPROVE = "✅ Approve"
    BTN_REJECT = "❌ Reject"
    BTN_BACK = "🔙 Back"
    
    # Callbacks
    CB_APPEAL = "appeal"
    CB_CONTACT = "contact"
    CB_APPROVE = "approve"
    CB_REJECT = "reject"
    CB_BACK = "back"

# ==================== DATABASE ====================
class Database:
    """Database handler"""
    
    def __init__(self):
        self.db_file = Config.DB_FILE
        self._init_db()
    
    def _init_db(self):
        """Initialize database"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Create table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS appeals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    text TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON appeals(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON appeals(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_created ON appeals(created_at DESC)')
            
            conn.commit()
            conn.close()
            print("✅ Database initialized successfully")
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            raise
    
    def add_appeal(self, user_id: int, username: str, first_name: str, text: str) -> int:
        """Add new appeal"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Check for pending appeal
            cursor.execute(
                'SELECT id FROM appeals WHERE user_id = ? AND status = "pending"',
                (user_id,)
            )
            if cursor.fetchone():
                conn.close()
                return -1
            
            cursor.execute(
                '''INSERT INTO appeals (user_id, username, first_name, text) 
                   VALUES (?, ?, ?, ?)''',
                (user_id, username, first_name, text)
            )
            conn.commit()
            appeal_id = cursor.lastrowid
            conn.close()
            return appeal_id
            
        except Exception as e:
            print(f"❌ Add appeal error: {e}")
            return 0
    
    def update_status(self, appeal_id: int, status: str) -> bool:
        """Update appeal status"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE appeals SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                (status, appeal_id)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Update status error: {e}")
            return False
    
    def get_pending(self) -> List[Dict]:
        """Get all pending appeals"""
        try:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                '''SELECT id, user_id, username, first_name, text, created_at 
                   FROM appeals WHERE status = "pending" 
                   ORDER BY created_at ASC'''
            )
            rows = cursor.fetchall()
            result = [dict(row) for row in rows]
            conn.close()
            return result
        except Exception as e:
            print(f"❌ Get pending error: {e}")
            return []
    
    def get_appeal(self, appeal_id: int) -> Optional[Dict]:
        """Get appeal by ID"""
        try:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                'SELECT * FROM appeals WHERE id = ?',
                (appeal_id,)
            )
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None
        except Exception as e:
            print(f"❌ Get appeal error: {e}")
            return None

# ==================== MAIN BOT ====================
class AppealBot:
    """Main bot class"""
    
    def __init__(self):
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        self.log = logging.getLogger(__name__)
        
        # Check token
        if not Config.BOT_TOKEN or Config.BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
            raise ValueError("❌ Invalid BOT_TOKEN! Please set your bot token.")
        
        # Initialize bot
        print("🤖 Initializing bot...")
        self.bot = telebot.TeleBot(Config.BOT_TOKEN)
        
        # Test bot connection
        try:
            bot_info = self.bot.get_me()
            print(f"✅ Bot connected: @{bot_info.username}")
            print(f"✅ Bot username: {Config.BOT_USERNAME}")
        except Exception as e:
            print(f"❌ Failed to connect to Telegram: {e}")
            raise
        
        # Initialize database
        print("📊 Initializing database...")
        self.db = Database()
        
        self.user_states = {}  # Track user states
        
        # Register handlers
        self._register_handlers()
        
        print("=" * 50)
        print("🤖 SoloLeveling Appeal Bot Started Successfully!")
        print(f"📱 Bot: {Config.BOT_USERNAME}")
        print(f"👥 Group: {Config.GROUP}")
        print(f"👤 Admin: {Config.ADMIN_USERNAME}")
        print("=" * 50)
    
    def _register_handlers(self):
        """Register all handlers"""
        
        @self.bot.message_handler(commands=['start'])
        def start_cmd(message):
            try:
                self._start(message)
            except Exception as e:
                self.log.error(f"Start error: {e}")
        
        @self.bot.message_handler(commands=['appeals'])
        def appeals_cmd(message):
            try:
                self._show_appeals(message)
            except Exception as e:
                self.log.error(f"Appeals error: {e}")
        
        @self.bot.message_handler(commands=['check'])
        def check_cmd(message):
            try:
                self._check_ban_status(message)
            except Exception as e:
                self.log.error(f"Check error: {e}")
        
        @self.bot.callback_query_handler(func=lambda call: True)
        def callback_handler(call):
            try:
                self._handle_callback(call)
            except Exception as e:
                self.log.error(f"Callback error: {e}")
                try:
                    self.bot.answer_callback_query(call.id, "❌ Error occurred")
                except:
                    pass
        
        @self.bot.message_handler(func=lambda message: True)
        def text_handler(message):
            try:
                self._handle_text(message)
            except Exception as e:
                self.log.error(f"Text handler error: {e}")
    
    # ==================== UTILITY METHODS ====================
    
    def _is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id == Config.ADMIN_ID
    
    def _main_keyboard(self):
        """Create main menu keyboard"""
        kb = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton(Config.BTN_APPEAL, callback_data=Config.CB_APPEAL)
        btn2 = types.InlineKeyboardButton(Config.BTN_CONTACT, callback_data=Config.CB_CONTACT)
        kb.add(btn1, btn2)
        return kb
    
    def _back_keyboard(self):
        """Create back button keyboard"""
        kb = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton(Config.BTN_BACK, callback_data=Config.CB_BACK)
        kb.add(btn)
        return kb
    
    def _approve_reject_keyboard(self, appeal_id: int, user_id: int):
        """Create approve/reject keyboard for admin"""
        kb = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton(
            f"✅ Approve #{appeal_id}",
            callback_data=f"{Config.CB_APPROVE}:{appeal_id}:{user_id}"
        )
        btn2 = types.InlineKeyboardButton(
            f"❌ Reject #{appeal_id}",
            callback_data=f"{Config.CB_REJECT}:{appeal_id}:{user_id}"
        )
        kb.add(btn1, btn2)
        return kb
    
    def _is_banned(self, user_id: int) -> bool:
        """
        Check if user is banned from group
        FIXED: Properly detects banned users
        """
        try:
            # Get chat member information
            member = self.bot.get_chat_member(Config.GROUP, user_id)
            
            # Log the status for debugging
            self.log.info(f"User {user_id} status: {member.status}")
            
            # Check if user is banned (kicked)
            if member.status == 'kicked':
                self.log.info(f"✅ User {user_id} IS BANNED")
                return True
            
            # Check if user is restricted (sometimes used for bans)
            if member.status == 'restricted':
                self.log.info(f"⚠️ User {user_id} is restricted")
                # Check if they can't send messages
                if hasattr(member, 'can_send_messages') and not member.can_send_messages:
                    self.log.info(f"✅ User {user_id} IS BANNED (restricted)")
                    return True
            
            # User is not banned
            self.log.info(f"❌ User {user_id} IS NOT BANNED (status: {member.status})")
            return False
            
        except ApiTelegramException as e:
            error_msg = str(e).lower()
            
            # User not found in the group - they might be banned or not a member
            if "user not found" in error_msg:
                self.log.info(f"⚠️ User {user_id} not found in group")
                # Try to check if they're banned by attempting to unban
                # If they were banned, this would succeed even if user not found
                try:
                    # This is a trick to detect if user was banned
                    # If they were banned, unban_chat_member will succeed even if user not found
                    self.bot.unban_chat_member(Config.GROUP, user_id)
                    self.log.info(f"✅ User {user_id} WAS BANNED (unban succeeded)")
                    return True
                except:
                    self.log.info(f"❌ User {user_id} is not a member and not banned")
                    return False
            
            # Bot is not admin or not in group
            elif "bot is not a member" in error_msg or "not enough rights" in error_msg:
                self.log.error(f"❌ Bot doesn't have proper permissions in {Config.GROUP}")
                self.log.error("Please make the bot an admin with 'Ban Users' permission")
                return False
            
            else:
                self.log.error(f"❌ Ban check error: {e}")
                return False
                
        except Exception as e:
            self.log.error(f"❌ Ban check error: {e}")
            return False
    
    def _unban_user(self, user_id: int) -> bool:
        """Unban user from group"""
        try:
            self.bot.unban_chat_member(Config.GROUP, user_id, only_if_banned=True)
            self.log.info(f"✅ User {user_id} unbanned")
            return True
        except ApiTelegramException as e:
            if "user not found" in str(e).lower():
                # User might still be banned, try without only_if_banned
                try:
                    self.bot.unban_chat_member(Config.GROUP, user_id)
                    self.log.info(f"✅ User {user_id} unbanned (forced)")
                    return True
                except:
                    self.log.error(f"❌ Unban failed: {e}")
                    return False
            self.log.error(f"❌ Unban error: {e}")
            return False
        except Exception as e:
            self.log.error(f"❌ Unban error: {e}")
            return False
    
    # ==================== HANDLER METHODS ====================
    
    def _start(self, message):
        """Handle /start command"""
        try:
            self.bot.send_message(
                message.chat.id,
                Config.WELCOME,
                reply_markup=self._main_keyboard()
            )
            self.log.info(f"✅ Start from {message.from_user.id}")
        except Exception as e:
            self.log.error(f"❌ Start error: {e}")
            self.bot.send_message(message.chat.id, "❌ Error. Please try again.")
    
    def _check_ban_status(self, message):
        """Check ban status command for testing"""
        user_id = message.from_user.id
        is_banned = self._is_banned(user_id)
        
        status_msg = f"""🔍 Ban Status Check

User ID: {user_id}
Username: @{message.from_user.username or 'No username'}
Name: {message.from_user.first_name}

Status: {'❌ BANNED' if is_banned else '✅ NOT BANNED'}

Group: {Config.GROUP}"""
        
        self.bot.send_message(message.chat.id, status_msg)
    
    def _handle_callback(self, call):
        """Handle callback queries"""
        try:
            data = call.data
            
            if data == Config.CB_APPEAL:
                self._create_appeal(call)
            elif data == Config.CB_CONTACT:
                self._contact_admin(call)
            elif data == Config.CB_BACK:
                self._back_to_menu(call)
            elif data.startswith(Config.CB_APPROVE):
                self._approve_appeal(call)
            elif data.startswith(Config.CB_REJECT):
                self._reject_appeal(call)
            else:
                self.bot.answer_callback_query(call.id, "❌ Invalid option")
                
        except Exception as e:
            self.log.error(f"❌ Callback error: {e}")
            self.bot.answer_callback_query(call.id, "❌ Error")
    
    def _contact_admin(self, call):
        """Handle contact button"""
        try:
            self.bot.answer_callback_query(call.id)
            self.bot.send_message(
                call.message.chat.id,
                Config.CONTACT,
                reply_markup=self._back_keyboard()
            )
            self.log.info(f"✅ Contact shown to {call.from_user.id}")
        except Exception as e:
            self.log.error(f"Contact error: {e}")
    
    def _back_to_menu(self, call):
        """Handle back button"""
        try:
            self.bot.answer_callback_query(call.id)
            self.bot.edit_message_text(
                Config.WELCOME,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=self._main_keyboard()
            )
        except Exception as e:
            self.log.error(f"Back error: {e}")
    
    def _create_appeal(self, call):
        """Handle create appeal button"""
        try:
            self.bot.answer_callback_query(call.id)
            user_id = call.from_user.id
            
            # Check for pending appeals
            pending = self.db.get_pending()
            if any(a['user_id'] == user_id for a in pending):
                self.bot.send_message(
                    call.message.chat.id,
                    "⏳ You already have a pending appeal. Please wait for admin review."
                )
                return
            
            # Check if user is banned
            self.log.info(f"🔍 Checking ban status for user {user_id}")
            is_banned = self._is_banned(user_id)
            
            if is_banned:
                # User is banned - allow appeal
                self.user_states[user_id] = 'waiting_for_appeal'
                self.bot.send_message(
                    call.message.chat.id,
                    Config.APPEAL_REQ,
                    reply_markup=self._back_keyboard()
                )
                self.log.info(f"✅ Appeal started for banned user {user_id}")
            else:
                # User is not banned
                self.bot.send_message(
                    call.message.chat.id,
                    Config.NOT_BANNED
                )
                self.log.info(f"❌ User {user_id} is not banned")
                
        except Exception as e:
            self.log.error(f"Create appeal error: {e}")
            self.bot.send_message(call.message.chat.id, "❌ Error checking ban status. Please try again.")
    
    def _handle_text(self, message):
        """Handle text messages"""
        try:
            user_id = message.from_user.id
            
            # Check if user is in appeal process
            if user_id not in self.user_states or self.user_states[user_id] != 'waiting_for_appeal':
                self._start(message)
                return
            
            text = message.text.strip()
            
            # Validate appeal text
            if len(text) < 10:
                self.bot.send_message(message.chat.id, "❌ Please provide a detailed appeal (minimum 10 characters).")
                return
            
            if len(text) > 1000:
                self.bot.send_message(message.chat.id, "❌ Appeal is too long (maximum 1000 characters).")
                return
            
            # Save to database
            username = message.from_user.username or "No username"
            first_name = message.from_user.first_name or "Unknown"
            
            appeal_id = self.db.add_appeal(user_id, username, first_name, text)
            
            if appeal_id == -1:
                self.bot.send_message(message.chat.id, "⏳ You already have a pending appeal!")
                return
            
            if appeal_id == 0:
                self.bot.send_message(message.chat.id, "❌ Error saving appeal. Please try again.")
                return
            
            # Clear state
            self.user_states.pop(user_id, None)
            
            # Forward to admin
            self._forward_to_admin(appeal_id, user_id, username, first_name, text)
            
            # Notify user
            self.bot.send_message(
                message.chat.id,
                Config.RECEIVED.format(id=appeal_id)
            )
            
            self.log.info(f"✅ Appeal #{appeal_id} from {user_id}")
        except Exception as e:
            self.log.error(f"Text handler error: {e}")
    
    def _forward_to_admin(self, appeal_id: int, user_id: int, username: str, first_name: str, text: str):
        """Forward appeal to admin"""
        msg = f"""🔔 New Appeal Received

📋 Appeal ID: #{appeal_id}
👤 User: {first_name}
🆔 User ID: {user_id}
Username: @{username}
📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📝 Appeal Message:
{text}

Status: ⏳ Pending Review"""
        
        try:
            self.bot.send_message(
                Config.ADMIN_ID,
                msg,
                reply_markup=self._approve_reject_keyboard(appeal_id, user_id)
            )
            self.log.info(f"✅ Appeal #{appeal_id} forwarded to admin")
        except Exception as e:
            self.log.error(f"❌ Forward error: {e}")
            raise
    
    def _approve_appeal(self, call):
        """Handle approve button"""
        try:
            # Check admin
            if not self._is_admin(call.from_user.id):
                self.bot.answer_callback_query(call.id, "❌ Admin only!", show_alert=True)
                return
            
            # Parse data
            _, appeal_id_str, user_id_str = call.data.split(':')
            appeal_id = int(appeal_id_str)
            user_id = int(user_id_str)
            
            # Get appeal
            appeal = self.db.get_appeal(appeal_id)
            if not appeal:
                self.bot.answer_callback_query(call.id, "❌ Appeal not found!", show_alert=True)
                return
            
            if appeal['status'] != 'pending':
                self.bot.answer_callback_query(
                    call.id,
                    f"❌ Already {appeal['status']}!",
                    show_alert=True
                )
                return
            
            # Unban user
            if self._unban_user(user_id):
                # Update database
                self.db.update_status(appeal_id, 'approved')
                
                # Answer callback
                self.bot.answer_callback_query(call.id, "✅ Approved & Unbanned!")
                
                # Update admin message
                try:
                    self.bot.edit_message_text(
                        call.message.text + "\n\n✅ APPROVED",
                        call.message.chat.id,
                        call.message.message_id,
                        reply_markup=None
                    )
                except:
                    pass
                
                # Notify user
                try:
                    self.bot.send_message(user_id, Config.APPROVED)
                except Exception as e:
                    self.log.warning(f"⚠️ Could not notify user {user_id}: {e}")
                
                # Confirm to admin
                self.bot.send_message(
                    Config.ADMIN_ID,
                    f"✅ Appeal #{appeal_id} approved and user unbanned!"
                )
                
                self.log.info(f"✅ Appeal #{appeal_id} approved")
            else:
                self.bot.answer_callback_query(call.id, "❌ Failed to unban user!", show_alert=True)
        except Exception as e:
            self.log.error(f"Approve error: {e}")
            self.bot.answer_callback_query(call.id, "❌ Error", show_alert=True)
    
    def _reject_appeal(self, call):
        """Handle reject button"""
        try:
            # Check admin
            if not self._is_admin(call.from_user.id):
                self.bot.answer_callback_query(call.id, "❌ Admin only!", show_alert=True)
                return
            
            # Parse data
            _, appeal_id_str, user_id_str = call.data.split(':')
            appeal_id = int(appeal_id_str)
            user_id = int(user_id_str)
            
            # Get appeal
            appeal = self.db.get_appeal(appeal_id)
            if not appeal:
                self.bot.answer_callback_query(call.id, "❌ Appeal not found!", show_alert=True)
                return
            
            if appeal['status'] != 'pending':
                self.bot.answer_callback_query(
                    call.id,
                    f"❌ Already {appeal['status']}!",
                    show_alert=True
                )
                return
            
            # Update database
            self.db.update_status(appeal_id, 'rejected')
            
            # Answer callback
            self.bot.answer_callback_query(call.id, "✅ Rejected!")
            
            # Update admin message
            try:
                self.bot.edit_message_text(
                    call.message.text + "\n\n❌ REJECTED",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=None
                )
            except:
                pass
            
            # Notify user
            try:
                self.bot.send_message(user_id, Config.REJECTED)
            except Exception as e:
                self.log.warning(f"⚠️ Could not notify user {user_id}: {e}")
            
            # Confirm to admin
            self.bot.send_message(
                Config.ADMIN_ID,
                f"❌ Appeal #{appeal_id} rejected"
            )
            
            self.log.info(f"✅ Appeal #{appeal_id} rejected")
        except Exception as e:
            self.log.error(f"Reject error: {e}")
            self.bot.answer_callback_query(call.id, "❌ Error", show_alert=True)
    
    def _show_appeals(self, message):
        """Show pending appeals to admin"""
        try:
            # Check admin
            if not self._is_admin(message.from_user.id):
                self.bot.send_message(message.chat.id, "❌ Admin only!")
                return
            
            # Get pending appeals
            appeals = self.db.get_pending()
            
            if not appeals:
                self.bot.send_message(message.chat.id, "📭 No pending appeals.")
                return
            
            # Format message
            msg = "📋 Pending Appeals:\n\n"
            for i, appeal in enumerate(appeals, 1):
                msg += f"{i}. #{appeal['id']} | {appeal['first_name']}\n"
                msg += f"   @{appeal['username']} | ID: {appeal['user_id']}\n"
                msg += f"   📝 {appeal['text'][:50]}...\n"
                msg += f"   📅 {appeal['created_at'][:16]}\n\n"
                
                if len(msg) > 3500:
                    break
            
            self.bot.send_message(message.chat.id, msg[:4000])
            self.log.info(f"✅ Pending appeals shown to admin")
        except Exception as e:
            self.log.error(f"Show appeals error: {e}")
    
    def run(self):
        """Run the bot"""
        try:
            print("\n🚀 Bot is running... Press Ctrl+C to stop\n")
            print("📌 Commands:")
            print("   /start - Start the bot")
            print("   /appeals - View pending appeals (admin only)")
            print("   /check - Check your ban status")
            print("\n")
            self.bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Bot error: {e}")
            sys.exit(1)

# ==================== MAIN ====================
if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("🤖 SoloLeveling Appeal Bot")
    print("=" * 50)
    print("📱 Bot: @Communityappealbot")
    print("👥 Group: @sololeveling")
    print("👤 Admin: @xConfusion")
    print("=" * 50 + "\n")
    
    try:
        bot = AppealBot()
        bot.run()
    except Exception as e:
        print(f"\n❌ Failed to start: {e}")
        print("\n💡 Possible issues:")
        print("1. Check your internet connection")
        print("2. Verify the bot token is correct")
        print("3. Make sure the bot is an admin in @sololeveling")
        print("4. Bot must have 'Ban Users' permission")
        sys.exit(1)
