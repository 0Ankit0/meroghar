import 'package:equatable/equatable.dart';
import 'listing_parsing.dart';

class ListingCategoryAttribute extends Equatable {
  final String id;
  final String name;
  final String slug;
  final String type;
  final bool isRequired;
  final bool isFilterable;
  final List<String> options;
  final int displayOrder;

  const ListingCategoryAttribute({
    required this.id,
    required this.name,
    required this.slug,
    required this.type,
    required this.isRequired,
    required this.isFilterable,
    this.options = const [],
    this.displayOrder = 0,
  });

  factory ListingCategoryAttribute.fromJson(Map<String, dynamic> json) {
    final options = <String>[];
    final rawOptions = readValue(json, ['options', 'options_json']);

    if (rawOptions is List) {
      options.addAll(rawOptions
          .map((option) => option.toString().trim())
          .where((option) => option.isNotEmpty));
    } else if (rawOptions is Map) {
      options.addAll(rawOptions.values
          .map((option) => option.toString().trim())
          .where((option) => option.isNotEmpty));
    }

    return ListingCategoryAttribute(
      id: readString(json, ['id', 'attribute_id']) ?? '',
      name: readString(json, ['name', 'label']) ?? 'Custom attribute',
      slug: readString(json, ['slug']) ??
          titleFromKey(readString(json, ['name', 'label']) ?? 'attribute')
              .toLowerCase()
              .replaceAll(' ', '_'),
      type: readString(json, ['attribute_type', 'type']) ?? 'text',
      isRequired: readBool(json, ['is_required', 'required']) ?? false,
      isFilterable: readBool(json, ['is_filterable', 'filterable']) ?? false,
      options: options,
      displayOrder:
          readInt(json, ['display_order', 'position', 'sort_order']) ?? 0,
    );
  }

  @override
  List<Object?> get props => [
        id,
        name,
        slug,
        type,
        isRequired,
        isFilterable,
        options,
        displayOrder,
      ];
}

class ListingCategory extends Equatable {
  final String id;
  final String name;
  final String slug;
  final String? description;
  final String? iconUrl;
  final bool isActive;
  final int displayOrder;
  final List<ListingCategoryAttribute> attributes;

  const ListingCategory({
    required this.id,
    required this.name,
    required this.slug,
    this.description,
    this.iconUrl,
    this.isActive = true,
    this.displayOrder = 0,
    this.attributes = const [],
  });

  factory ListingCategory.fromJson(Map<String, dynamic> json) {
    final rawAttributes =
        readList(json, ['attributes', 'property_type_features', 'features']);
    final attributes = rawAttributes
        .map((item) => ListingCategoryAttribute.fromJson(asJsonMap(item)))
        .where((attribute) => attribute.name.isNotEmpty)
        .toList()
      ..sort((a, b) => a.displayOrder.compareTo(b.displayOrder));

    return ListingCategory(
      id: readString(json, ['id', 'category_id', 'property_type_id']) ?? '',
      name: readString(json, ['name', 'label']) ?? 'Category',
      slug: readString(json, ['slug']) ??
          titleFromKey(readString(json, ['name']) ?? 'category')
              .toLowerCase()
              .replaceAll(' ', '-'),
      description: readString(json, ['description']),
      iconUrl: readString(json, ['icon_url', 'icon']),
      isActive: readBool(json, ['is_active', 'active']) ?? true,
      displayOrder:
          readInt(json, ['display_order', 'position', 'sort_order']) ?? 0,
      attributes: attributes,
    );
  }

  @override
  List<Object?> get props => [
        id,
        name,
        slug,
        description,
        iconUrl,
        isActive,
        displayOrder,
        attributes,
      ];
}
