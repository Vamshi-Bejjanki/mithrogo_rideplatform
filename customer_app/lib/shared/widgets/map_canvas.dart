import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../app/theme/app_colors.dart';
import '../../core/location/lat_lng.dart';

/// Stylised street map drawn with CustomPaint, so no map SDK or API key is needed.
/// Swap for a real map widget later; the callers only pass coordinates.
class MapCanvas extends StatefulWidget {
  const MapCanvas({
    super.key,
    this.pickup,
    this.drop,
    this.captain,
    this.showPulse = false,
  });

  final LatLng? pickup;
  final LatLng? drop;
  final LatLng? captain;

  /// Draws a radar pulse around the pickup point while searching for a captain.
  final bool showPulse;

  @override
  State<MapCanvas> createState() => _MapCanvasState();
}

class _MapCanvasState extends State<MapCanvas> with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 2400),
  )..repeat();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        return CustomPaint(
          size: Size.infinite,
          painter: _MapPainter(
            pickup: widget.pickup,
            drop: widget.drop,
            captain: widget.captain,
            pulse: widget.showPulse ? _controller.value : null,
          ),
        );
      },
    );
  }
}

class _MapPainter extends CustomPainter {
  _MapPainter({this.pickup, this.drop, this.captain, this.pulse});

  final LatLng? pickup;
  final LatLng? drop;
  final LatLng? captain;
  final double? pulse;

  static const _padding = 90.0;

  @override
  void paint(Canvas canvas, Size size) {
    _paintBase(canvas, size);

    final points = [pickup, drop, captain].whereType<LatLng>().toList();
    if (points.isEmpty) return;

    final project = _projector(points, size);
    final pickupPoint = pickup == null ? null : project(pickup!);
    final dropPoint = drop == null ? null : project(drop!);
    final captainPoint = captain == null ? null : project(captain!);

    if (pickupPoint != null && dropPoint != null) {
      _paintRoute(canvas, pickupPoint, dropPoint);
    }
    if (pickupPoint != null && pulse != null) {
      _paintPulse(canvas, pickupPoint, pulse!);
    }
    if (pickupPoint != null) {
      _paintPickup(canvas, pickupPoint);
    }
    if (dropPoint != null) {
      _paintDrop(canvas, dropPoint);
    }
    if (captainPoint != null) {
      _paintCaptain(canvas, captainPoint);
    }
  }

  void _paintBase(Canvas canvas, Size size) {
    final rect = Offset.zero & size;
    canvas.drawRect(rect, Paint()..color = AppColors.mapBackground);

    // Parks and water, as fixed blocks.
    final park = Paint()..color = AppColors.mapPark;
    final water = Paint()..color = AppColors.mapWater;
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromLTWH(size.width * 0.06, size.height * 0.1, size.width * 0.3, size.height * 0.18),
        const Radius.circular(18),
      ),
      park,
    );
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromLTWH(size.width * 0.62, size.height * 0.68, size.width * 0.42, size.height * 0.2),
        const Radius.circular(24),
      ),
      water,
    );

    // Road grid: two weights, offset so it doesn't look like a perfect plan.
    final major = Paint()
      ..color = AppColors.mapRoad
      ..strokeWidth = 16
      ..strokeCap = StrokeCap.round;
    final minor = Paint()
      ..color = AppColors.mapRoad
      ..strokeWidth = 7
      ..strokeCap = StrokeCap.round;

    for (final f in const [0.22, 0.58, 0.9]) {
      final y = size.height * f;
      canvas.drawLine(Offset(-20, y), Offset(size.width + 20, y + size.height * 0.04), major);
    }
    for (final f in const [0.15, 0.48, 0.82]) {
      final x = size.width * f;
      canvas.drawLine(Offset(x, -20), Offset(x - size.width * 0.05, size.height + 20), major);
    }
    for (final f in const [0.38, 0.72]) {
      final y = size.height * f;
      canvas.drawLine(Offset(0, y), Offset(size.width, y - size.height * 0.02), minor);
    }
    for (final f in const [0.32, 0.65]) {
      final x = size.width * f;
      canvas.drawLine(Offset(x, 0), Offset(x + size.width * 0.03, size.height), minor);
    }
  }

  /// Maps lat/lng to canvas pixels so every point fits inside the padding.
  Offset Function(LatLng) _projector(List<LatLng> points, Size size) {
    var minLat = points.first.latitude;
    var maxLat = points.first.latitude;
    var minLng = points.first.longitude;
    var maxLng = points.first.longitude;
    for (final p in points) {
      minLat = math.min(minLat, p.latitude);
      maxLat = math.max(maxLat, p.latitude);
      minLng = math.min(minLng, p.longitude);
      maxLng = math.max(maxLng, p.longitude);
    }
    // A single point gets a small window around it instead of a zero-size box.
    final latSpan = math.max(maxLat - minLat, 0.012);
    final lngSpan = math.max(maxLng - minLng, 0.012);
    final centerLat = (maxLat + minLat) / 2;
    final centerLng = (maxLng + minLng) / 2;
    final usableW = size.width - _padding * 2;
    final usableH = size.height - _padding * 2;

    return (LatLng p) {
      final x = size.width / 2 + ((p.longitude - centerLng) / lngSpan) * usableW;
      final y = size.height / 2 - ((p.latitude - centerLat) / latSpan) * usableH;
      return Offset(x, y);
    };
  }

  void _paintRoute(Canvas canvas, Offset from, Offset to) {
    // Elbow route, like a road path, not a straight line.
    final path = Path()
      ..moveTo(from.dx, from.dy)
      ..lineTo(to.dx, from.dy)
      ..lineTo(to.dx, to.dy);

    canvas.drawPath(
      path,
      Paint()
        ..color = AppColors.ink.withValues(alpha: 0.18)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 11
        ..strokeJoin = StrokeJoin.round,
    );
    canvas.drawPath(
      path,
      Paint()
        ..color = AppColors.ink
        ..style = PaintingStyle.stroke
        ..strokeWidth = 5
        ..strokeJoin = StrokeJoin.round
        ..strokeCap = StrokeCap.round,
    );
  }

  void _paintPulse(Canvas canvas, Offset center, double t) {
    for (var i = 0; i < 3; i++) {
      final phase = (t + i / 3) % 1;
      final radius = 18 + phase * 130;
      final alpha = (1 - phase) * 0.35;
      canvas.drawCircle(
        center,
        radius,
        Paint()..color = AppColors.brand.withValues(alpha: alpha),
      );
    }
  }

  void _paintPickup(Canvas canvas, Offset center) {
    canvas.drawCircle(center, 11, Paint()..color = AppColors.onInk);
    canvas.drawCircle(center, 7, Paint()..color = AppColors.ink);
  }

  void _paintDrop(Canvas canvas, Offset center) {
    const half = 9.0;
    final square = Rect.fromCenter(center: center, width: half * 2, height: half * 2);
    canvas.drawRect(square.inflate(3), Paint()..color = AppColors.onInk);
    canvas.drawRect(square, Paint()..color = AppColors.ink);
  }

  void _paintCaptain(Canvas canvas, Offset center) {
    canvas.drawCircle(center, 20, Paint()..color = AppColors.ink.withValues(alpha: 0.2));
    canvas.drawCircle(center, 16, Paint()..color = AppColors.brand);
    canvas.drawCircle(
      center,
      16,
      Paint()
        ..color = AppColors.ink
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2,
    );
  }

  @override
  bool shouldRepaint(covariant _MapPainter old) {
    return old.pickup != pickup ||
        old.drop != drop ||
        old.captain != captain ||
        old.pulse != pulse;
  }
}
