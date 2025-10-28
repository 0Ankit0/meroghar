/// SQLite local database service for offline-first functionality.
/// Implements T019 from tasks.md.
library;

import 'dart:async';
import 'dart:io';

import 'package:path/path.dart';
import 'package:sqflite/sqflite.dart';

import '../config/env.example.dart';

/// Database service for managing local SQLite database.
///
/// Provides offline-first functionality with automatic schema creation
/// and migration support.
class DatabaseService {
  factory DatabaseService() => instance;

  DatabaseService._internal();
  static final DatabaseService instance = DatabaseService._internal();
  static Database? _database;

  /// Get database instance, initializing if needed.
  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDatabase();
    return _database!;
  }

  /// Initialize database with schema.
  Future<Database> _initDatabase() async {
    final databasesPath = await getDatabasesPath();
    final path = join(databasesPath, Environment.localDbName);

    return await openDatabase(
      path,
      version: Environment.localDbVersion,
      onCreate: _onCreate,
      onUpgrade: _onUpgrade,
      onConfigure: _onConfigure,
    );
  }

  /// Configure database settings.
  Future<void> _onConfigure(Database db) async {
    // Enable foreign keys
    await db.execute('PRAGMA foreign_keys = ON');
  }

  /// Create initial database schema.
  Future<void> _onCreate(Database db, int version) async {
    await db.transaction((txn) async {
      // Device metadata table for sync tracking
      await txn.execute('''
        CREATE TABLE device_metadata (
          key TEXT PRIMARY KEY,
          value TEXT NOT NULL,
          updated_at TEXT NOT NULL
        )
      ''');

      // Users table
      await txn.execute('''
        CREATE TABLE users (
          id TEXT PRIMARY KEY,
          email TEXT NOT NULL UNIQUE,
          phone TEXT,
          full_name TEXT NOT NULL,
          role TEXT NOT NULL,
          is_active INTEGER NOT NULL DEFAULT 1,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          last_synced_at TEXT
        )
      ''');

      // Properties table
      await txn.execute('''
        CREATE TABLE properties (
          id TEXT PRIMARY KEY,
          owner_id TEXT NOT NULL,
          name TEXT NOT NULL,
          address_line1 TEXT NOT NULL,
          address_line2 TEXT,
          city TEXT NOT NULL,
          state TEXT NOT NULL,
          postal_code TEXT NOT NULL,
          country TEXT NOT NULL,
          total_units INTEGER NOT NULL,
          base_currency TEXT NOT NULL,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          last_synced_at TEXT,
          FOREIGN KEY (owner_id) REFERENCES users (id)
        )
      ''');

      // Tenants table
      await txn.execute('''
        CREATE TABLE tenants (
          id TEXT PRIMARY KEY,
          user_id TEXT NOT NULL,
          property_id TEXT NOT NULL,
          monthly_rent REAL NOT NULL,
          security_deposit REAL,
          start_date TEXT NOT NULL,
          end_date TEXT,
          is_active INTEGER NOT NULL DEFAULT 1,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          last_synced_at TEXT,
          FOREIGN KEY (user_id) REFERENCES users (id),
          FOREIGN KEY (property_id) REFERENCES properties (id)
        )
      ''');

      // Payments table
      await txn.execute('''
        CREATE TABLE payments (
          id TEXT PRIMARY KEY,
          tenant_id TEXT NOT NULL,
          amount REAL NOT NULL,
          payment_date TEXT NOT NULL,
          payment_method TEXT NOT NULL,
          status TEXT NOT NULL,
          notes TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          last_synced_at TEXT,
          FOREIGN KEY (tenant_id) REFERENCES tenants (id)
        )
      ''');

      // Bills table
      await txn.execute('''
        CREATE TABLE bills (
          id TEXT PRIMARY KEY,
          property_id TEXT NOT NULL,
          bill_type TEXT NOT NULL,
          total_amount REAL NOT NULL,
          billing_period TEXT NOT NULL,
          due_date TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          last_synced_at TEXT,
          FOREIGN KEY (property_id) REFERENCES properties (id)
        )
      ''');

      // Bill Allocations table
      await txn.execute('''
        CREATE TABLE bill_allocations (
          id TEXT PRIMARY KEY,
          bill_id TEXT NOT NULL,
          tenant_id TEXT NOT NULL,
          amount REAL NOT NULL,
          is_paid INTEGER NOT NULL DEFAULT 0,
          paid_at TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          last_synced_at TEXT,
          FOREIGN KEY (bill_id) REFERENCES bills (id),
          FOREIGN KEY (tenant_id) REFERENCES tenants (id)
        )
      ''');

      // Expenses table
      await txn.execute('''
        CREATE TABLE expenses (
          id TEXT PRIMARY KEY,
          property_id TEXT NOT NULL,
          category TEXT NOT NULL,
          amount REAL NOT NULL,
          description TEXT,
          receipt_url TEXT,
          expense_date TEXT NOT NULL,
          created_by TEXT NOT NULL,
          approved_by TEXT,
          status TEXT NOT NULL,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          last_synced_at TEXT,
          FOREIGN KEY (property_id) REFERENCES properties (id)
        )
      ''');

      // Documents table
      await txn.execute('''
        CREATE TABLE documents (
          id TEXT PRIMARY KEY,
          tenant_id TEXT,
          property_id TEXT,
          document_type TEXT NOT NULL,
          file_url TEXT NOT NULL,
          file_name TEXT NOT NULL,
          expiration_date TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          last_synced_at TEXT
        )
      ''');

      // Sync Queue table (for offline operations)
      await txn.execute('''
        CREATE TABLE sync_queue (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          operation TEXT NOT NULL,
          entity_type TEXT NOT NULL,
          entity_id TEXT NOT NULL,
          data TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'pending',
          retry_count INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL,
          last_attempt_at TEXT
        )
      ''');

      // Create indexes for better query performance
      await txn.execute('CREATE INDEX idx_users_email ON users(email)');
      await txn.execute('CREATE INDEX idx_users_role ON users(role)');
      await txn.execute('CREATE INDEX idx_users_is_active ON users(is_active)');
      await txn.execute('CREATE INDEX idx_tenants_user_id ON tenants(user_id)');
      await txn.execute(
          'CREATE INDEX idx_tenants_property_id ON tenants(property_id)');
      await txn
          .execute('CREATE INDEX idx_tenants_is_active ON tenants(is_active)');
      await txn.execute(
          'CREATE INDEX idx_tenants_start_date ON tenants(start_date)');
      await txn.execute(
          'CREATE INDEX idx_payments_tenant_id ON payments(tenant_id)');
      await txn.execute('CREATE INDEX idx_payments_status ON payments(status)');
      await txn.execute(
          'CREATE INDEX idx_payments_payment_date ON payments(payment_date)');
      await txn
          .execute('CREATE INDEX idx_bills_property_id ON bills(property_id)');
      await txn.execute(
          'CREATE INDEX idx_bills_billing_period ON bills(billing_period)');
      await txn.execute('CREATE INDEX idx_bills_due_date ON bills(due_date)');
      await txn.execute(
          'CREATE INDEX idx_bill_allocations_bill_id ON bill_allocations(bill_id)');
      await txn.execute(
          'CREATE INDEX idx_bill_allocations_tenant_id ON bill_allocations(tenant_id)');
      await txn.execute(
          'CREATE INDEX idx_bill_allocations_is_paid ON bill_allocations(is_paid)');
      await txn.execute(
          'CREATE INDEX idx_expenses_property_id ON expenses(property_id)');
      await txn
          .execute('CREATE INDEX idx_expenses_category ON expenses(category)');
      await txn.execute('CREATE INDEX idx_expenses_status ON expenses(status)');
      await txn.execute(
          'CREATE INDEX idx_expenses_expense_date ON expenses(expense_date)');
      await txn.execute(
          'CREATE INDEX idx_documents_tenant_id ON documents(tenant_id)');
      await txn.execute(
          'CREATE INDEX idx_documents_property_id ON documents(property_id)');
      await txn.execute(
          'CREATE INDEX idx_documents_document_type ON documents(document_type)');
      await txn
          .execute('CREATE INDEX idx_sync_queue_status ON sync_queue(status)');
      await txn.execute(
          'CREATE INDEX idx_sync_queue_entity ON sync_queue(entity_type, entity_id)');
      await txn.execute(
          'CREATE INDEX idx_sync_queue_created_at ON sync_queue(created_at)');
    });
  }

  /// Handle database schema upgrades.
  Future<void> _onUpgrade(Database db, int oldVersion, int newVersion) async {
    // Add migration logic here as needed
    // Example:
    // if (oldVersion < 2) {
    //   await db.execute('ALTER TABLE users ADD COLUMN new_field TEXT');
    // }
  }

  /// Close database connection.
  Future<void> close() async {
    final db = await database;
    await db.close();
    _database = null;
  }

  /// Clear all data from database (use with caution).
  Future<void> clearAllData() async {
    final db = await database;
    await db.transaction((txn) async {
      await txn.delete('sync_queue');
      await txn.delete('documents');
      await txn.delete('expenses');
      await txn.delete('bill_allocations');
      await txn.delete('bills');
      await txn.delete('payments');
      await txn.delete('tenants');
      await txn.delete('properties');
      await txn.delete('users');
    });
  }

  /// Delete database file (for testing/logout).
  Future<void> deleteDatabase() async {
    final databasesPath = await getDatabasesPath();
    final path = join(databasesPath, Environment.localDbName);

    if (await File(path).exists()) {
      await File(path).delete();
    }
    _database = null;
  }

  /// Get device metadata value by key.
  Future<String?> getDeviceMetadata(String key) async {
    final db = await database;
    final result = await db.query(
      'device_metadata',
      columns: ['value'],
      where: 'key = ?',
      whereArgs: [key],
    );

    if (result.isNotEmpty) {
      return result.first['value'] as String;
    }
    return null;
  }

  /// Set device metadata value.
  Future<void> setDeviceMetadata(String key, String value) async {
    final db = await database;
    await db.insert(
      'device_metadata',
      {
        'key': key,
        'value': value,
        'updated_at': DateTime.now().toIso8601String(),
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  /// Get device ID, generating one if it doesn't exist.
  Future<String> getDeviceId() async {
    var deviceId = await getDeviceMetadata('device_id');

    if (deviceId == null) {
      // Generate a new UUID for this device
      deviceId = _generateUuid();
      await setDeviceMetadata('device_id', deviceId);
    }

    return deviceId;
  }

  /// Get device name for display.
  Future<String?> getDeviceName() async =>
      await getDeviceMetadata('device_name');

  /// Set device name for display.
  Future<void> setDeviceName(String name) async {
    await setDeviceMetadata('device_name', name);
  }

  /// Simple UUID generator (v4-like).
  String _generateUuid() {
    final now = DateTime.now().millisecondsSinceEpoch;
    final random = (now * 1000).toString();
    return 'device-$random-${_randomString(8)}';
  }

  /// Generate random string for UUID.
  String _randomString(int length) {
    const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
    final random = DateTime.now().microsecondsSinceEpoch;
    return List.generate(length, (i) => chars[(random + i) % chars.length])
        .join();
  }
}
