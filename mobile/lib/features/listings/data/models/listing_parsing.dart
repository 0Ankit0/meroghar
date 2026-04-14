Map<String, dynamic> asJsonMap(dynamic value) {
  if (value is Map<String, dynamic>) return value;
  if (value is Map) {
    return value.map((key, value) => MapEntry(key.toString(), value));
  }
  return const <String, dynamic>{};
}

List<dynamic> asJsonList(dynamic value) {
  if (value is List<dynamic>) return value;
  if (value is List) return List<dynamic>.from(value);
  return const <dynamic>[];
}

dynamic readValue(Map<String, dynamic> json, Iterable<String> keys) {
  for (final key in keys) {
    if (json.containsKey(key) && json[key] != null) {
      return json[key];
    }
  }
  return null;
}

String? readString(Map<String, dynamic> json, Iterable<String> keys) {
  final value = readValue(json, keys);
  if (value == null) return null;
  final stringValue = value.toString().trim();
  if (stringValue.isEmpty) return null;
  return stringValue;
}

double? readDouble(Map<String, dynamic> json, Iterable<String> keys) {
  final value = readValue(json, keys);
  if (value == null) return null;
  if (value is num) return value.toDouble();
  if (value is String) {
    return double.tryParse(value.replaceAll(',', '').trim());
  }
  return null;
}

int? readInt(Map<String, dynamic> json, Iterable<String> keys) {
  final value = readValue(json, keys);
  if (value == null) return null;
  if (value is int) return value;
  if (value is num) return value.toInt();
  if (value is String) {
    return int.tryParse(value.trim());
  }
  return null;
}

bool? readBool(Map<String, dynamic> json, Iterable<String> keys) {
  final value = readValue(json, keys);
  if (value == null) return null;
  if (value is bool) return value;
  if (value is num) return value != 0;
  if (value is String) {
    switch (value.trim().toLowerCase()) {
      case 'true':
      case 'yes':
      case 'y':
      case '1':
        return true;
      case 'false':
      case 'no':
      case 'n':
      case '0':
        return false;
    }
  }
  return null;
}

DateTime? readDateTime(Map<String, dynamic> json, Iterable<String> keys) {
  final value = readValue(json, keys);
  if (value == null) return null;
  if (value is DateTime) return value;
  if (value is int) {
    if (value > 1000000000000) {
      return DateTime.fromMillisecondsSinceEpoch(value);
    }
    return DateTime.fromMillisecondsSinceEpoch(value * 1000);
  }
  if (value is String) {
    return DateTime.tryParse(value);
  }
  return null;
}

Map<String, dynamic> readMap(Map<String, dynamic> json, Iterable<String> keys) {
  final value = readValue(json, keys);
  final map = asJsonMap(value);
  if (map.isNotEmpty) return map;
  return const <String, dynamic>{};
}

List<dynamic> readList(Map<String, dynamic> json, Iterable<String> keys) {
  final value = readValue(json, keys);
  final list = asJsonList(value);
  if (list.isNotEmpty) return list;
  return const <dynamic>[];
}

List<String> readStringList(Map<String, dynamic> json, Iterable<String> keys) {
  final value = readValue(json, keys);
  if (value is List) {
    return value
        .map((item) => item.toString().trim())
        .where((item) => item.isNotEmpty)
        .toList();
  }
  if (value is String && value.trim().isNotEmpty) {
    return [value.trim()];
  }
  return const <String>[];
}

String titleFromKey(String key) {
  final cleaned = key
      .replaceAll(RegExp(r'[_-]+'), ' ')
      .replaceAll(RegExp(r'\s+'), ' ')
      .trim();
  if (cleaned.isEmpty) return key;

  return cleaned.split(' ').map((part) {
    if (part.isEmpty) return part;
    return '${part[0].toUpperCase()}${part.substring(1)}';
  }).join(' ');
}
