"use client";

import { useEffect, useRef } from "react";
import type { LatLngExpression, Map as LeafletMap, LayerGroup } from "leaflet";

export type MapMarker = {
  id: string;
  position: [number, number];
  color: string;
  radius?: number;
  popup?: string;
};

export type MapLine = { id: string; points: [number, number][]; color: string; dashed?: boolean; weight?: number };

/**
 * Leaflet map on OpenStreetMap tiles. Loaded in the browser only (Leaflet needs `window`).
 * Fits to the content once; later updates keep the viewer's pan and zoom.
 */
export default function MapView({ markers, lines = [], className = "map", center = [18.6725, 78.094] }: {
  markers: MapMarker[]; lines?: MapLine[]; className?: string; center?: [number, number];
}) {
  const element = useRef<HTMLDivElement>(null);
  const map = useRef<LeafletMap | null>(null);
  const layer = useRef<LayerGroup | null>(null);
  const fitted = useRef(false);
  const leaflet = useRef<typeof import("leaflet") | null>(null);

  useEffect(() => {
    let cancelled = false;
    let observer: ResizeObserver | null = null;
    import("leaflet").then((L) => {
      if (cancelled || !element.current || map.current) return;
      leaflet.current = L;
      map.current = L.map(element.current).setView(center as LatLngExpression, 13);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap contributors",
      }).addTo(map.current);
      layer.current = L.layerGroup().addTo(map.current);
      // Leaflet measures its box once; re-measure whenever the layout settles or the window resizes.
      observer = new ResizeObserver(() => map.current?.invalidateSize());
      observer.observe(element.current);
      draw();
    });
    return () => {
      cancelled = true;
      observer?.disconnect();
      map.current?.remove();
      map.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function draw() {
    const L = leaflet.current;
    if (!L || !layer.current || !map.current) return;
    layer.current.clearLayers();
    const bounds: [number, number][] = [];
    lines.forEach((line) => {
      if (line.points.length < 2) return;
      L.polyline(line.points, { color: line.color, weight: line.weight ?? 3, dashArray: line.dashed ? "4 6" : undefined })
        .addTo(layer.current!);
      bounds.push(...line.points);
    });
    markers.forEach((m) => {
      const marker = L.circleMarker(m.position, {
        radius: m.radius ?? 7, color: m.color, fillColor: m.color, fillOpacity: 0.85, weight: 2,
      }).addTo(layer.current!);
      if (m.popup) marker.bindPopup(m.popup);
      bounds.push(m.position);
    });
    if (!fitted.current && bounds.length) {
      map.current.fitBounds(bounds, { padding: [40, 40], maxZoom: 15 });
      fitted.current = true;
    }
  }

  useEffect(draw, [markers, lines]); // eslint-disable-line react-hooks/exhaustive-deps

  return <div ref={element} className={className} />;
}

export function esc(text: unknown) {
  return String(text ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]!);
}
