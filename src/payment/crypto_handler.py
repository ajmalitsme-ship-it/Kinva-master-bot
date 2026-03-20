"""
Crypto Payment Handler - Cryptocurrency payments for global users
Author: @kinva_master
"""

import os
import logging
import hashlib
import json
import qrcode
import base64
from io import BytesIO
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import requests

from ..config import Config
from ..database import db

logger = logging.getLogger(__name__)

class CryptoHandler:
    """Cryptocurrency payment processing for global users"""
    
    def __init__(self):
        # Supported cryptocurrencies
        self.cryptocurrencies = {
            'btc': {
                'name': 'Bitcoin',
                'symbol': 'BTC',
                'icon': '₿',
                'network': 'Bitcoin',
                'min_amount': 0.0001,
                'confirmations': 2,
                'explorer': 'https://blockchain.info/tx/',
                'api': 'https://blockchain.info/q/addressbalance/'
            },
            'eth': {
                'name': 'Ethereum',
                'symbol': 'ETH',
                'icon': 'Ξ',
                'network': 'Ethereum (ERC-20)',
                'min_amount': 0.01,
                'confirmations': 12,
                'explorer': 'https://etherscan.io/tx/',
                'api': 'https://api.etherscan.io/api'
            },
            'usdt': {
                'name': 'Tether USD',
                'symbol': 'USDT',
                'icon': '₮',
                'network': 'Tron (TRC-20)',
                'min_amount': 10,
                'confirmations': 1,
                'explorer': 'https://tronscan.org/#/transaction/',
                'api': 'https://api.trongrid.io/v1/accounts/'
            },
            'usdc': {
                'name': 'USD Coin',
                'symbol': 'USDC',
                'icon': '💵',
                'network': 'Ethereum (ERC-20)',
                'min_amount': 10,
                'confirmations': 12,
                'explorer': 'https://etherscan.io/tx/',
                'api': 'https://api.etherscan.io/api'
            },
            'ltc': {
                'name': 'Litecoin',
                'symbol': 'LTC',
                'icon': 'Ł',
                'network': 'Litecoin',
                'min_amount': 0.1,
                'confirmations': 6,
                'explorer': 'https://chain.so/tx/LTC/',
                'api': 'https://chain.so/api/v2/get_address_balance/LTC/'
            },
            'doge': {
                'name': 'Dogecoin',
                'symbol': 'DOGE',
                'icon': '🐕',
                'network': 'Dogecoin',
                'min_amount': 50,
                'confirmations': 40,
                'explorer': 'https://dogechain.info/tx/',
                'api': 'https://dogechain.info/api/v1/address/balance/'
            },
            'bnb': {
                'name': 'Binance Coin',
                'symbol': 'BNB',
                'icon': '🟡',
                'network': 'BSC (BEP-20)',
                'min_amount': 0.1,
                'confirmations': 15,
                'explorer': 'https://bscscan.com/tx/',
                'api': 'https://api.bscscan.com/api'
            },
            'sol': {
                'name': 'Solana',
                'symbol': 'SOL',
                'icon': '◎',
                'network': 'Solana',
                'min_amount': 0.5,
                'confirmations': 32,
                'explorer': 'https://explorer.solana.com/tx/',
                'api': 'https://api.mainnet-beta.solana.com'
            },
            'matic': {
                'name': 'Polygon',
                'symbol': 'MATIC',
                'icon': '🔷',
                'network': 'Polygon (MATIC)',
                'min_amount': 10,
                'confirmations': 64,
                'explorer': 'https://polygonscan.com/tx/',
                'api': 'https://api.polygonscan.com/api'
            },
            'xrp': {
                'name': 'Ripple',
                'symbol': 'XRP',
                'icon': '💧',
                'network': 'XRP Ledger',
                'min_amount': 10,
                'confirmations': 4,
                'explorer': 'https://xrpscan.com/tx/',
                'api': 'https://data.ripple.com/v2/accounts/'
            }
        }
        
        # Wallet addresses for each cryptocurrency
        self.wallet_addresses = {
            'btc': Config.BTC_WALLET or '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa',
            'eth': Config.ETH_WALLET or '0x742d35Cc6634C0532925a3b844Bc9eC8fB9b9b5c',
            'usdt': Config.USDT_WALLET or 'TNeHyNvTfqXyYkYyQgRqZqQgQqQqQqQqQq',
            'usdc': Config.USDC_WALLET or '0x742d35Cc6634C0532925a3b844Bc9eC8fB9b9b5c',
            'ltc': Config.LTC_WALLET or 'LbTjMGN7gELw4KbeyQf6cTCq859hD18guE',
            'doge': Config.DOGE_WALLET or 'D5KjV5kYjJq5QyRqZqQgQqQqQqQqQqQq',
            'bnb': Config.BNB_WALLET or '0x742d35Cc6634C0532925a3b844Bc9eC8fB9b9b5c',
            'sol': Config.SOL_WALLET or '7Ec4JhYjKqWqYkYyQgRqZqQgQqQqQqQqQq',
            'matic': Config.MATIC_WALLET or '0x742d35Cc6634C0532925a3b844Bc9eC8fB9b9b5c',
            'xrp': Config.XRP_WALLET or 'rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh'
        }
        
        # Exchange rates (USD to crypto) - updated periodically
        self.exchange_rates = {
            'btc': 50000,
            'eth': 3000,
            'usdt': 1,
            'usdc': 1,
            'ltc': 100,
            'doge': 0.1,
            'bnb': 300,
            'sol': 100,
            'matic': 1,
            'xrp': 0.5
        }
        
        # API keys for blockchain explorers
        self.api_keys = {
            'etherscan': Config.ETHERSCAN_API_KEY,
            'bscscan': Config.BSCSCAN_API_KEY,
            'polygonscan': Config.POLYGONSCAN_API_KEY
        }
    
    def create_payment(self, user_id: int, amount_inr: float, 
                       plan: str, currency: str = 'usdt') -> Dict:
        """Create crypto payment request"""
        try:
            crypto = self.cryptocurrencies.get(currency.lower())
            if not crypto:
                raise ValueError(f"Unsupported cryptocurrency: {currency}")
            
            # Calculate crypto amount based on current exchange rate
            rate = self.exchange_rates.get(currency.lower(), 0)
            if rate == 0:
                raise ValueError(f"Exchange rate not available for {currency}")
            
            amount_crypto = amount_inr / rate
            
            # Check minimum amount
            if amount_crypto < crypto['min_amount']:
                raise ValueError(f"Minimum amount is {crypto['min_amount']} {crypto['symbol']}")
            
            # Create payment record
            payment_id = db.create_payment(
                user_id=user_id,
                amount=amount_inr,
                currency='INR',
                plan=plan,
                method='crypto',
                status='pending',
                crypto_currency=currency.upper(),
                crypto_amount=amount_crypto,
                crypto_address=self.wallet_addresses.get(currency.lower())
            )
            
            # Generate payment address (in production, generate unique address per user)
            # For demo, use fixed wallet address
            payment_address = self.wallet_addresses.get(currency.lower())
            
            return {
                'payment_id': payment_id,
                'currency': currency.upper(),
                'amount': amount_crypto,
                'amount_inr': amount_inr,
                'address': payment_address,
                'network': crypto['network'],
                'min_amount': crypto['min_amount'],
                'confirmations': crypto['confirmations'],
                'expires_in': 3600,  # 1 hour
                'exchange_rate': rate,
                'crypto_info': crypto
            }
            
        except Exception as e:
            logger.error(f"Create crypto payment error: {e}")
            raise
    
    def generate_qr(self, payment_data: Dict) -> str:
        """Generate QR code for crypto payment address"""
        try:
            address = payment_data['address']
            amount = payment_data['amount']
            currency = payment_data['currency'].lower()
            
            # Create crypto URI
            if currency == 'btc':
                uri = f"bitcoin:{address}?amount={amount}"
            elif currency == 'eth':
                uri = f"ethereum:{address}?value={amount}"
            elif currency == 'usdt' or currency == 'usdc':
                uri = f"{currency}:{address}?amount={amount}"
            elif currency == 'ltc':
                uri = f"litecoin:{address}?amount={amount}"
            elif currency == 'doge':
                uri = f"dogecoin:{address}?amount={amount}"
            elif currency == 'bnb':
                uri = f"binance:{address}?amount={amount}"
            elif currency == 'sol':
                uri = f"solana:{address}?amount={amount}"
            else:
                uri = address
            
            # Generate QR
            qr = qrcode.QRCode(version=2, box_size=10, border=4)
            qr.add_data(uri)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            qr_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            return qr_base64
            
        except Exception as e:
            logger.error(f"Generate QR error: {e}")
            return None
    
    def verify_payment(self, payment_id: str, tx_hash: str = None) -> Dict:
        """Verify crypto payment on blockchain"""
        try:
            payment = db.get_payment(payment_id)
            if not payment:
                return {'status': 'failed', 'message': 'Payment not found'}
            
            if payment['status'] == 'completed':
                return {'status': 'success', 'message': 'Payment already verified'}
            
            currency = payment['crypto_currency'].lower()
            expected_amount = payment['crypto_amount']
            address = payment['crypto_address']
            
            # Check blockchain for transactions
            is_paid, tx_info = self._check_blockchain(currency, address, expected_amount, tx_hash)
            
            if is_paid:
                # Update payment status
                db.update_payment(payment_id, {
                    'status': 'completed',
                    'transaction_hash': tx_info.get('hash'),
                    'confirmations': tx_info.get('confirmations', 0),
                    'verified_at': datetime.now().isoformat()
                })
                
                # Activate premium based on plan
                plan = payment['plan']
                if plan == 'lifetime':
                    db.activate_lifetime_premium(payment['user_id'])
                else:
                    months = self._get_months_from_plan(plan)
                    db.activate_premium(payment['user_id'], months=months)
                
                # Create notification
                db.create_notification(
                    user_id=payment['user_id'],
                    title='Crypto Payment Received! 🎉',
                    message=f'Your {payment["crypto_currency"]} payment of {expected_amount} has been confirmed. Premium activated!',
                    type='success'
                )
                
                return {
                    'status': 'success',
                    'message': f'{plan.capitalize()} plan activated',
                    'transaction': tx_info
                }
            else:
                return {
                    'status': 'pending',
                    'message': 'Payment not detected yet',
                    'required': expected_amount,
                    'currency': currency.upper()
                }
            
        except Exception as e:
            logger.error(f"Verify payment error: {e}")
            return {'status': 'failed', 'message': str(e)}
    
    def _check_blockchain(self, currency: str, address: str, 
                          expected_amount: float, tx_hash: str = None) -> tuple:
        """Check blockchain for incoming transactions"""
        try:
            if currency == 'btc':
                return self._check_btc(address, expected_amount, tx_hash)
            elif currency == 'eth':
                return self._check_eth(address, expected_amount, tx_hash)
            elif currency == 'usdt':
                return self._check_usdt(address, expected_amount, tx_hash)
            elif currency == 'ltc':
                return self._check_ltc(address, expected_amount, tx_hash)
            elif currency == 'doge':
                return self._check_doge(address, expected_amount, tx_hash)
            else:
                return False, {}
                
        except Exception as e:
            logger.error(f"Blockchain check error: {e}")
            return False, {}
    
    def _check_btc(self, address: str, expected: float, tx_hash: str = None) -> tuple:
        """Check Bitcoin blockchain"""
        try:
            if tx_hash:
                # Check specific transaction
                url = f"https://blockchain.info/rawtx/{tx_hash}"
                response = requests.get(url)
                if response.status_code == 200:
                    tx = response.json()
                    total_out = sum(out['value'] for out in tx['out']) / 100000000
                    if total_out >= expected:
                        return True, {'hash': tx_hash, 'amount': total_out, 'confirmations': tx.get('block_height')}
                return False, {}
            else:
                # Check address balance
                url = f"https://blockchain.info/q/addressbalance/{address}"
                response = requests.get(url)
                if response.status_code == 200:
                    balance = int(response.text) / 100000000
                    if balance >= expected:
                        return True, {'balance': balance}
                return False, {}
                
        except Exception as e:
            logger.error(f"BTC check error: {e}")
            return False, {}
    
    def _check_eth(self, address: str, expected: float, tx_hash: str = None) -> tuple:
        """Check Ethereum blockchain"""
        try:
            api_key = self.api_keys.get('etherscan')
            if tx_hash:
                url = f"https://api.etherscan.io/api?module=transaction&action=gettxreceiptstatus&txhash={tx_hash}&apikey={api_key}"
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('result', {}).get('status') == '1':
                        return True, {'hash': tx_hash}
                return False, {}
            else:
                url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&sort=desc&apikey={api_key}"
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == '1':
                        for tx in data.get('result', [])[:10]:
                            value = int(tx.get('value', 0)) / 1e18
                            if value >= expected and tx.get('to', '').lower() == address.lower():
                                return True, {'hash': tx['hash'], 'amount': value}
                return False, {}
                
        except Exception as e:
            logger.error(f"ETH check error: {e}")
            return False, {}
    
    def _check_usdt(self, address: str, expected: float, tx_hash: str = None) -> tuple:
        """Check USDT (TRC-20) blockchain"""
        try:
            if tx_hash:
                url = f"https://api.trongrid.io/v1/transactions/{tx_hash}"
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('data'):
                        return True, {'hash': tx_hash}
                return False, {}
            else:
                url = f"https://api.trongrid.io/v1/accounts/{address}/transactions"
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    for tx in data.get('data', [])[:10]:
                        if tx.get('raw_data', {}).get('contract', []):
                            contract = tx['raw_data']['contract'][0]
                            if contract.get('type') == 'TransferContract':
                                amount = contract.get('parameter', {}).get('value', {}).get('amount', 0) / 1e6
                                if amount >= expected:
                                    return True, {'hash': tx['txID'], 'amount': amount}
                return False, {}
                
        except Exception as e:
            logger.error(f"USDT check error: {e}")
            return False, {}
    
    def _check_ltc(self, address: str, expected: float, tx_hash: str = None) -> tuple:
        """Check Litecoin blockchain"""
        try:
            if tx_hash:
                url = f"https://chain.so/api/v2/get_tx/LTC/{tx_hash}"
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'success':
                        return True, {'hash': tx_hash}
                return False, {}
            else:
                url = f"https://chain.so/api/v2/get_address_balance/LTC/{address}"
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'success':
                        balance = float(data.get('data', {}).get('confirmed_balance', 0))
                        if balance >= expected:
                            return True, {'balance': balance}
                return False, {}
                
        except Exception as e:
            logger.error(f"LTC check error: {e}")
            return False, {}
    
    def _check_doge(self, address: str, expected: float, tx_hash: str = None) -> tuple:
        """Check Dogecoin blockchain"""
        try:
            if tx_hash:
                url = f"https://dogechain.info/api/v1/transaction/{tx_hash}"
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success') == 1:
                        return True, {'hash': tx_hash}
                return False, {}
            else:
                url = f"https://dogechain.info/api/v1/address/balance/{address}"
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    balance = float(data.get('balance', 0)) / 100000000
                    if balance >= expected:
                        return True, {'balance': balance}
                return False, {}
                
        except Exception as e:
            logger.error(f"DOGE check error: {e}")
            return False, {}
    
    def _get_months_from_plan(self, plan: str) -> int:
        """Convert plan to months"""
        months_map = {
            'monthly': 1,
            'quarterly': 3,
            'half_yearly': 6,
            'yearly': 12
        }
        return months_map.get(plan, 1)
    
    def get_exchange_rates(self) -> Dict:
        """Get current exchange rates for all cryptocurrencies"""
        return self.exchange_rates
    
    def update_exchange_rates(self) -> Dict:
        """Update exchange rates from external API"""
        try:
            # In production, fetch from CoinGecko or similar API
            # For demo, use static rates
            return self.exchange_rates
        except Exception as e:
            logger.error(f"Update exchange rates error: {e}")
            return self.exchange_rates
    
    def get_crypto_list(self) -> List[Dict]:
        """Get list of supported cryptocurrencies"""
        return [
            {
                'code': code,
                'name': crypto['name'],
                'symbol': crypto['symbol'],
                'icon': crypto['icon'],
                'network': crypto['network'],
                'min_amount': crypto['min_amount']
            }
            for code, crypto in self.cryptocurrencies.items()
        ]
    
    def get_transaction_details(self, currency: str, tx_hash: str) -> Dict:
        """Get transaction details from blockchain"""
        try:
            currency = currency.lower()
            crypto = self.cryptocurrencies.get(currency)
            if not crypto:
                return {'error': 'Currency not supported'}
            
            explorer_url = f"{crypto['explorer']}{tx_hash}"
            
            return {
                'hash': tx_hash,
                'explorer_url': explorer_url,
                'currency': crypto['symbol'],
                'network': crypto['network']
            }
            
        except Exception as e:
            logger.error(f"Get transaction details error: {e}")
            return {'error': str(e)}

# Create global instance
crypto_handler = CryptoHandler()
