/// Screen to list maintenance requests.
library;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';

import '../../providers/maintenance_provider.dart';
import '../../models/maintenance_request.dart';
import '../../config/app_router.dart';
import '../../config/constants.dart';

class MaintenanceListScreen extends StatefulWidget {
  const MaintenanceListScreen({super.key});

  @override
  State<MaintenanceListScreen> createState() => _MaintenanceListScreenState();
}

class _MaintenanceListScreenState extends State<MaintenanceListScreen> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() {
      context.read<MaintenanceProvider>().loadRequests();
    });
  }

  Future<void> _refresh() async {
    await context.read<MaintenanceProvider>().loadRequests();
  }

  void _navigateToCreate() {
    Navigator.pushNamed(context, AppRoutes.maintenanceCreate).then((_) {
      _refresh();
    });
  }

  @override
  Widget build(BuildContext context) {
     return Scaffold(
      appBar: AppBar(
        title: const Text('Maintenance Requests'),
        actions: [
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: _navigateToCreate,
          ),
        ],
      ),
      body: Consumer<MaintenanceProvider>(
        builder: (context, provider, _) {
          if (provider.isLoading && provider.requests.isEmpty) {
            return const Center(child: CircularProgressIndicator());
          }

          if (provider.hasError) {
             return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.error_outline, size: 48, color: Colors.red),
                  const SizedBox(height: 16),
                  Text(provider.error!),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: _refresh,
                    child: const Text('Retry'),
                  ),
                ],
              ),
            );
          }

          if (provider.requests.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.build_circle_outlined, size: 64, color: Colors.grey),
                  const SizedBox(height: 16),
                  const Text('No maintenance requests found'),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: _navigateToCreate,
                    child: const Text('Submit Request'),
                  ),
                ],
              ),
            );
          }

          return RefreshIndicator(
            onRefresh: _refresh,
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: provider.requests.length,
              itemBuilder: (context, index) {
                final req = provider.requests[index];
                return MaintenanceRequestCard(request: req);
              },
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _navigateToCreate,
        child: const Icon(Icons.add),
      ),
    );
  }
}

class MaintenanceRequestCard extends StatelessWidget {
  const MaintenanceRequestCard({super.key, required this.request});

  final MaintenanceRequest request;

  Color _getStatusColor(MaintenanceStatus status) {
    switch (status) {
      case MaintenanceStatus.open: return Colors.blue;
      case MaintenanceStatus.inProgress: return Colors.orange;
      case MaintenanceStatus.resolved: return Colors.green;
      case MaintenanceStatus.closed: return Colors.grey;
    }
  }
  
  Color _getPriorityColor(MaintenancePriority priority) {
    switch (priority) {
       case MaintenancePriority.urgent: return Colors.red;
       case MaintenancePriority.high: return Colors.deepOrange;
       case MaintenancePriority.medium: return Colors.orange;
       case MaintenancePriority.low: return Colors.green;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: () {
          // Navigate to details
             Navigator.pushNamed(
            context,
            AppRoutes.maintenanceDetail.replaceAll(':id', request.id),
            arguments: request, // Pass object directly or ID
          );
        },
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Text(
                      request.title,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: _getStatusColor(request.status).withOpacity(0.1),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      request.status.label,
                      style: TextStyle(
                        color: _getStatusColor(request.status),
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                request.description,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Colors.grey[600],
                ),
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                   Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      border: Border.all(color: _getPriorityColor(request.priority)),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      request.priority.label,
                      style: TextStyle(
                        color: _getPriorityColor(request.priority),
                        fontSize: 10,
                      ),
                    ),
                  ),
                  const Spacer(),
                  Text(
                    DateFormat('MMM d, yyyy').format(request.createdAt),
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
