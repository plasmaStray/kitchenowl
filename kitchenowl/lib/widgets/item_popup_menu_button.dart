import 'package:material_ui/material_ui.dart';
import 'package:kitchenowl/kitchenowl.dart';
import 'package:kitchenowl/models/category.dart';
import 'package:kitchenowl/models/household.dart';
import 'package:kitchenowl/models/item.dart';
import 'package:kitchenowl/pages/icon_selection_page.dart';
import 'package:kitchenowl/pages/item_search_page.dart';

enum _ItemAction {
  changeIcon,
  changeCategory,
  rename,
  merge,
  delete;
}

class ItemPopupMenuButton extends StatelessWidget {
  final Item item;
  final Household? household;
  final void Function(String?) setIcon;
  final List<Category>? categories;
  final Future<void> Function(Category?)? setCategory;
  final void Function(String) setName;
  final void Function(Item) mergeItem;
  final void Function() deleteItem;
  final ValueChanged<bool>? onMenuVisibilityChanged;

  const ItemPopupMenuButton({
    super.key,
    required this.item,
    this.household,
    required this.setIcon,
    this.categories,
    this.setCategory,
    required this.setName,
    required this.mergeItem,
    required this.deleteItem,
    this.onMenuVisibilityChanged,
  });

  @override
  Widget build(BuildContext context) {
    return PopupMenuButton<_ItemAction>(
      icon: const Icon(Icons.more_vert_rounded),
      onOpened: () => onMenuVisibilityChanged?.call(true),
      onCanceled: () => onMenuVisibilityChanged?.call(false),
      onSelected: (action) async {
        try {
          await _handleItemAction(context, action);
        } finally {
          onMenuVisibilityChanged?.call(false);
        }
      },
      itemBuilder: (context) => <PopupMenuEntry<_ItemAction>>[
        if (household != null)
          PopupMenuItem<_ItemAction>(
            value: _ItemAction.changeIcon,
            child: Text(AppLocalizations.of(context)!.changeIcon),
          ),
        if (categories != null && setCategory != null)
          PopupMenuItem<_ItemAction>(
            value: _ItemAction.changeCategory,
            child: Text(AppLocalizations.of(context)!.changeCategory),
          ),
        if (item is! RecipeItem && item.id != null)
          PopupMenuItem<_ItemAction>(
            value: _ItemAction.rename,
            child: Text(AppLocalizations.of(context)!.rename),
          ),
        if (item is! RecipeItem && item.id != null) const PopupMenuDivider(),
        if (household != null && item.id != null && item is! RecipeItem)
          PopupMenuItem<_ItemAction>(
            value: _ItemAction.merge,
            child: Text(AppLocalizations.of(context)!.merge),
          ),
        if (item is! RecipeItem && item.id != null)
          PopupMenuItem<_ItemAction>(
            value: _ItemAction.delete,
            child: Text(AppLocalizations.of(context)!.delete),
          ),
      ],
    );
  }

  Future<void> _handleItemAction(
      BuildContext context, _ItemAction action) async {
    switch (action) {
      case _ItemAction.changeIcon:
        final icon = await Navigator.of(context)
            .push<Nullable<String?>>(MaterialPageRoute(
          builder: (context) => IconSelectionPage(
            oldIcon: item.icon,
            name: item.name,
          ),
        ));
        if (icon != null) setIcon(icon.value);
        break;
      case _ItemAction.changeCategory:
        final category = await showDialog<Nullable<Category?>>(
          context: context,
          builder: (context) {
            Category? selectedCategory = item.category;
            return StatefulBuilder(
              builder: (context, setState) => AlertDialog(
                title: Text(AppLocalizations.of(context)!.changeCategory),
                content: DropdownButton<Category?>(
                  value: selectedCategory,
                  isExpanded: true,
                  items: [
                    DropdownMenuItem(
                      value: null,
                      child: Text(AppLocalizations.of(context)!.none),
                    ),
                    for (final category in categories!)
                      DropdownMenuItem(
                        value: category,
                        child: Text(category.name),
                      ),
                  ],
                  onChanged: (category) =>
                      setState(() => selectedCategory = category),
                ),
                actions: [
                  TextButton(
                    onPressed: () => Navigator.of(context).pop(),
                    child: Text(AppLocalizations.of(context)!.cancel),
                  ),
                  TextButton(
                    onPressed: () =>
                        Navigator.of(context).pop(Nullable(selectedCategory)),
                    child: Text(AppLocalizations.of(context)!.done),
                  ),
                ],
              ),
            );
          },
        );
        if (category != null && category.value != item.category) {
          await setCategory!(category.value);
        }
        break;
      case _ItemAction.rename:
        final res = await showDialog<String>(
          context: context,
          builder: (BuildContext context) {
            return TextDialog(
              title: AppLocalizations.of(context)!.categoryEdit,
              doneText: AppLocalizations.of(context)!.rename,
              hintText: AppLocalizations.of(context)!.name,
              initialText: item.name,
              isInputValid: (s) => s.trim().isNotEmpty && s != item.name,
            );
          },
        );
        if (res != null) setName(res);
        break;
      case _ItemAction.merge:
        final items = await Navigator.of(
              context,
              rootNavigator: true,
            ).push<List<Item>>(MaterialPageRoute(
              builder: (context) => ItemSearchPage(
                household: household!,
                multiple: false,
                title: AppLocalizations.of(context)!.itemsMerge,
              ),
            )) ??
            [];
        if (items.length == 1 && items.first.id != item.id) {
          final confirmed = await askForConfirmation(
            context: context,
            title: Text(
              AppLocalizations.of(context)!.itemsMerge,
            ),
            confirmText: AppLocalizations.of(context)!.merge,
            content: Text(
              AppLocalizations.of(context)!.itemsMergeConfirmation(
                item.name,
                items.first.name,
              ),
            ),
          );
          if (confirmed) {
            mergeItem(items.first);
          }
        }
        break;
      case _ItemAction.delete:
        final confirmed = await askForConfirmation(
          context: context,
          title: Text(
            AppLocalizations.of(context)!.itemDelete,
          ),
          content: Text(
            AppLocalizations.of(context)!.itemDeleteConfirmation(item.name),
          ),
        );
        if (confirmed) {
          deleteItem();
        }
        break;
    }
  }
}
