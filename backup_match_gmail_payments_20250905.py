# Backup of match_gmail_payments_to_passes() function from utils.py
# Created: 2025-09-05
# Original location: utils.py lines 932-1109

def match_gmail_payments_to_passes():
    from utils import extract_interac_transfers, get_setting, notify_pass_event
    from models import EbankPayment, Passport, db
    from datetime import datetime, timezone
    from flask import current_app
    from rapidfuzz import fuzz
    import imaplib

    with current_app.app_context():
        user = get_setting("MAIL_USERNAME")
        pwd = get_setting("MAIL_PASSWORD")

        if not user or not pwd:
            print("❌ MAIL_USERNAME or MAIL_PASSWORD is not set.")
            return

        threshold = int(get_setting("BANK_EMAIL_NAME_CONFIDANCE", "85"))
        processed_folder = get_setting("GMAIL_LABEL_FOLDER_PROCESSED", "PaymentProcessed")

        # Get IMAP server from settings, fallback to MAIL_SERVER or Gmail
        imap_server = get_setting("IMAP_SERVER")
        if not imap_server:
            mail_server = get_setting("MAIL_SERVER")
            if mail_server:
                # Try to use the mail server for IMAP (often works for custom domains)
                imap_server = mail_server
            else:
                # Fallback to Gmail for backward compatibility
                imap_server = "imap.gmail.com"
        
        print(f"🔌 Connecting to IMAP server: {imap_server}")
        
        try:
            # Try SSL connection first (port 993)
            mail = imaplib.IMAP4_SSL(imap_server)
        except:
            # If SSL fails, try TLS (port 143)
            print(f"⚠️ SSL connection failed, trying TLS...")
            mail = imaplib.IMAP4(imap_server, 143)
            mail.starttls()
        
        mail.login(user, pwd)
        mail.select("inbox")

        matches = extract_interac_transfers(user, pwd, mail)
        
        print(f"🔍 DEBUG: Found {len(matches)} email matches")
        for i, match in enumerate(matches):
            print(f"🔍 Email {i+1}: {match.get('subject', 'No subject')[:50]}...")

        for match in matches:
            name = match["bank_info_name"]
            amt = match["bank_info_amt"]
            from_email = match.get("from_email")
            uid = match.get("uid")
            subject = match["subject"]
            
            print(f"🔍 Processing payment: Name='{name}', Amount=${amt}, From={from_email}")

            best_score = 0
            best_passport = None
            unpaid_passports = Passport.query.filter_by(paid=False).all()
            
            print(f"🔍 Found {len(unpaid_passports)} unpaid passports to match against")

            for p in unpaid_passports:
                if not p.user:
                    continue  # Safety check
                score = fuzz.partial_ratio(name.lower(), p.user.name.lower())
                print(f"🔍 Checking passport: User='{p.user.name}', Amount=${p.sold_amt}, Score={score} (threshold={threshold})")
                if score >= threshold and abs(p.sold_amt - amt) < 1:
                    print(f"✅ MATCH FOUND! Score={score}, Amount match: ${p.sold_amt} ≈ ${amt}")
                    if score > best_score:
                        best_score = score
                        best_passport = p
                else:
                    if score < threshold:
                        print(f"❌ Score too low: {score} < {threshold}")
                    if abs(p.sold_amt - amt) >= 1:
                        print(f"❌ Amount mismatch: ${p.sold_amt} vs ${amt} (diff: ${abs(p.sold_amt - amt)})")

            if best_passport:
                print(f"🎯 PROCESSING MATCH: {best_passport.user.name} - ${best_passport.sold_amt}")
            else:
                print(f"❌ NO MATCH FOUND for payment: Name='{name}', Amount=${amt}")
                
            if best_passport:
                now_utc = datetime.now(timezone.utc)
                best_passport.paid = True
                best_passport.paid_date = now_utc
                db.session.add(best_passport)

                db.session.add(EbankPayment(
                    from_email=from_email,
                    subject=subject,
                    bank_info_name=name,
                    bank_info_amt=amt,
                    matched_pass_id=best_passport.id,
                    matched_name=best_passport.user.name,
                    matched_amt=best_passport.sold_amt,
                    name_score=best_score,
                    result="MATCHED",
                    mark_as_paid=True,
                    note="Matched by Gmail Bot."
                ))

                db.session.commit()

                notify_pass_event(
                    app=current_app._get_current_object(),
                    event_type="payment_received",
                    pass_data=best_passport,  # ✅ update keyword
                    activity=best_passport.activity,
                    admin_email="gmail-bot@system",
                    timestamp=now_utc
                )

                # Emit SSE notification for payment
                try:
                    from api.notifications import emit_payment_notification
                    emit_payment_notification(best_passport)
                except Exception as e:
                    print(f"⚠️ Failed to emit payment notification: {e}")

                if uid:
                    # Check if the processed folder exists, create if needed
                    try:
                        # List all folders to check if our processed folder exists
                        folder_exists = False
                        result, folder_list = mail.list()
                        if result == 'OK':
                            for folder_info in folder_list:
                                if folder_info:
                                    # Parse folder name from IMAP list response
                                    folder_str = folder_info.decode() if isinstance(folder_info, bytes) else folder_info
                                    # Check if our folder name appears in the response
                                    if processed_folder in folder_str:
                                        folder_exists = True
                                        break
                        
                        # Create folder if it doesn't exist
                        if not folder_exists:
                            print(f"📁 Creating folder: {processed_folder}")
                            try:
                                mail.create(processed_folder)
                            except Exception as create_error:
                                # Some servers don't allow folder creation or folder already exists
                                print(f"⚠️ Could not create folder {processed_folder}: {create_error}")
                        
                        # Try to copy the email to the processed folder
                        copy_result = mail.uid("COPY", uid, processed_folder)
                        if copy_result[0] == 'OK':
                            # Only mark as deleted if copy was successful
                            mail.uid("STORE", uid, "+FLAGS", "(\\Deleted)")
                            print(f"✅ Email moved to {processed_folder} folder")
                        else:
                            print(f"⚠️ Could not copy email to {processed_folder}: {copy_result}")
                            # Don't delete if we couldn't copy
                            
                    except Exception as e:
                        print(f"⚠️ Error moving email to processed folder: {e}")
                        # Don't delete the email if we couldn't move it
            else:
                db.session.add(EbankPayment(
                    from_email=from_email,
                    subject=subject,
                    bank_info_name=name,
                    bank_info_amt=amt,
                    name_score=0,
                    result="NO_MATCH",
                    mark_as_paid=False,
                    note="No matching passport found."
                ))

        db.session.commit()
        mail.expunge()
        mail.logout()