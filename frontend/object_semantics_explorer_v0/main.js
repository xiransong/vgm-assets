import "./style.css";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { FBXLoader } from "three/examples/jsm/loaders/FBXLoader.js";

const AXIS_OPTIONS = ["+x", "-x", "+y", "-y", "+z", "-z"];
const REVIEW_STATUS_OPTIONS = ["auto", "reviewed", "uncertain", "rejected"];
const REVIEW_SCOPE_ITEMS_V0 = [
  {
    id: "asset_role",
    label: "Role",
    description: "Whether the asset is reviewed as a parent_object or child_object.",
  },
  {
    id: "category",
    label: "Category",
    description: "The semantic object category such as coffee_table, mug, or bowl.",
  },
  {
    id: "front_axis",
    label: "Front axis",
    description: "The object-local facing direction used for orientation-sensitive placement.",
  },
  {
    id: "up_axis",
    label: "Up axis",
    description: "The upright object-local axis used to interpret the mesh and support logic.",
  },
  {
    id: "bottom_support_surface",
    label: "Bottom support surface",
    description: "The reviewed base footprint that should contact a supporting surface.",
  },
  {
    id: "support_surfaces_v1",
    label: "Support surfaces",
    description: "The reviewed top or shelf support rectangles used for placing child objects.",
  },
  {
    id: "canonical_bounds",
    label: "Canonical bounds",
    description: "The reviewed metric size used as the canonical object bounds in the explorer.",
  },
];
const REVIEW_SCOPE_TARGET_IDS_V0 = REVIEW_SCOPE_ITEMS_V0.map((item) => item.id);

const state = {
  assets: [],
  reviewQueue: null,
  currentAssetId: null,
  currentDetail: null,
  workingAsset: null,
  renderToken: 0,
  advancedVisible: false,
  surfaceXRay: false,
  visualLift: false,
};

const elements = {
  assetList: document.getElementById("asset-list"),
  queueSummary: document.getElementById("queue-summary"),
  assetTitle: document.getElementById("asset-title"),
  assetSubtitle: document.getElementById("asset-subtitle"),
  detailMeta: document.getElementById("detail-meta"),
  editorForm: document.getElementById("editor-form"),
  saveButton: document.getElementById("save-button"),
  resetAutoButton: document.getElementById("reset-auto-button"),
  acceptButton: document.getElementById("accept-button"),
  needsFixButton: document.getElementById("needs-fix-button"),
  rejectButton: document.getElementById("reject-button"),
  toggleXRayButton: document.getElementById("toggle-xray-button"),
  toggleLiftButton: document.getElementById("toggle-lift-button"),
  quickReviewNotes: document.getElementById("quick-review-notes"),
  reviewBadge: document.getElementById("review-badge"),
  reviewScopeList: document.getElementById("review-scope-list"),
  toggleAdvancedButton: document.getElementById("toggle-advanced-button"),
  viewerStatus: document.getElementById("viewer-status"),
  canvas: document.getElementById("viewer-canvas"),
};

const renderer = new THREE.WebGLRenderer({
  canvas: elements.canvas,
  antialias: true,
  alpha: true,
});
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(45, 1, 0.01, 100);
camera.position.set(1.6, 1.3, 1.8);
const fbxLoader = new FBXLoader();
const reviewMeshCache = new Map();

const controls = new OrbitControls(camera, elements.canvas);
controls.enableDamping = true;
controls.target.set(0, 0.35, 0);

scene.add(new THREE.AmbientLight(0xffffff, 1.3));
const sun = new THREE.DirectionalLight(0xffffff, 1.1);
sun.position.set(2.4, 3.4, 2.0);
scene.add(sun);
scene.add(new THREE.GridHelper(4, 16, 0x8ea49e, 0xd0d8cf));

const overlayRoot = new THREE.Group();
scene.add(overlayRoot);
scene.add(new THREE.AxesHelper(0.45));

function setCanvasSize() {
  const { clientWidth, clientHeight } = elements.canvas;
  renderer.setSize(clientWidth, clientHeight, false);
  camera.aspect = clientWidth / clientHeight;
  camera.updateProjectionMatrix();
}

window.addEventListener("resize", setCanvasSize);
setCanvasSize();

function animate() {
  controls.update();
  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}
animate();

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }
  return response.json();
}

function clearGroup(group) {
  while (group.children.length) {
    const child = group.children[group.children.length - 1];
    group.remove(child);
  }
}

function axisVector(axis) {
  switch (axis) {
    case "+x":
      return new THREE.Vector3(1, 0, 0);
    case "-x":
      return new THREE.Vector3(-1, 0, 0);
    case "+y":
      return new THREE.Vector3(0, 1, 0);
    case "-y":
      return new THREE.Vector3(0, -1, 0);
    case "+z":
      return new THREE.Vector3(0, 0, 1);
    case "-z":
      return new THREE.Vector3(0, 0, -1);
    default:
      return new THREE.Vector3(0, 1, 0);
  }
}

function planeQuaternion(normalAxis, frontAxis) {
  const up = axisVector(normalAxis).normalize();
  const forwardGuess = axisVector(frontAxis).normalize();
  const right = new THREE.Vector3().crossVectors(forwardGuess, up).normalize();
  if (right.lengthSq() < 1e-6) {
    return new THREE.Quaternion();
  }
  const forward = new THREE.Vector3().crossVectors(up, right).normalize();
  const basis = new THREE.Matrix4().makeBasis(right, up, forward);
  return new THREE.Quaternion().setFromRotationMatrix(basis);
}

function addPlaneOverlay({
  width,
  depth,
  position,
  normalAxis,
  frontAxis,
  color,
  opacity = 0.22,
  labelText = null,
  displayOffsetSign = 1,
}) {
  const displayOffset = state.visualLift
    ? axisVector(normalAxis).normalize().multiplyScalar(Math.max(Math.min(width, depth) * 0.025, 0.012) * displayOffsetSign)
    : new THREE.Vector3(0, 0, 0);
  const displayPosition = position.clone().add(displayOffset);
  const mesh = new THREE.Mesh(
    new THREE.BoxGeometry(width, 0.01, depth),
    new THREE.MeshStandardMaterial({
      color,
      transparent: true,
      opacity,
      roughness: 0.75,
      metalness: 0.0,
    }),
  );
  mesh.position.copy(displayPosition);
  const quaternion = planeQuaternion(normalAxis, frontAxis);
  mesh.quaternion.copy(quaternion);
  overlayRoot.add(mesh);

  const edges = new THREE.LineSegments(
    new THREE.EdgesGeometry(new THREE.BoxGeometry(width, 0.01, depth)),
    new THREE.LineBasicMaterial({ color }),
  );
  edges.position.copy(displayPosition);
  edges.quaternion.copy(quaternion);
  overlayRoot.add(edges);

  if (labelText) {
    const sideDirection = new THREE.Vector3(1, 0, 0).applyQuaternion(quaternion).normalize();
    const labelOffset = sideDirection.multiplyScalar(width / 2 + 0.08);
    labelOffset.add(new THREE.Vector3(0, 0.025, 0));
    const sprite = makeTextSprite(labelText, color, 0.22, 0.055);
    sprite.position.copy(displayPosition.clone().add(labelOffset));
    overlayRoot.add(sprite);
  }
}

function makeTextSprite(text, color, width = 0.45, height = 0.11) {
  const canvas = document.createElement("canvas");
  canvas.width = 512;
  canvas.height = 128;
  const context = canvas.getContext("2d");
  context.fillStyle = "rgba(248, 246, 238, 0.92)";
  context.fillRect(0, 0, canvas.width, canvas.height);
  context.strokeStyle = `#${color.toString(16).padStart(6, "0")}`;
  context.lineWidth = 8;
  context.strokeRect(8, 8, canvas.width - 16, canvas.height - 16);
  context.fillStyle = "#1f2a25";
  context.font = "36px IBM Plex Sans";
  context.textAlign = "center";
  context.textBaseline = "middle";
  context.fillText(text, canvas.width / 2, canvas.height / 2);
  const texture = new THREE.CanvasTexture(canvas);
  const material = new THREE.SpriteMaterial({ map: texture, transparent: true });
  const sprite = new THREE.Sprite(material);
  sprite.scale.set(width, height, 1);
  return sprite;
}

function axisHalfExtent(axis, proxy) {
  switch (axis) {
    case "+x":
    case "-x":
      return proxy.width_m / 2;
    case "+y":
    case "-y":
      return proxy.height_m / 2;
    case "+z":
    case "-z":
      return proxy.depth_m / 2;
    default:
      return Math.max(proxy.width_m, proxy.height_m, proxy.depth_m) / 2;
  }
}

function addAxisArrowOverlay({
  origin,
  axis,
  length,
  color,
  label,
}) {
  const direction = axisVector(axis).normalize();
  const arrow = new THREE.ArrowHelper(direction, origin, length, color, length * 0.18, length * 0.1);
  overlayRoot.add(arrow);
  const labelSprite = makeTextSprite(label, color, 0.18, 0.05);
  labelSprite.position.copy(
    origin.clone().add(direction.multiplyScalar(length + 0.08)),
  );
  overlayRoot.add(labelSprite);
}

function addObjectAxisOverlays(proxy, asset) {
  if (!proxy) {
    return;
  }
  const center = new THREE.Vector3(proxy.center_m.x, proxy.center_m.y, proxy.center_m.z);
  const maxExtent = Math.max(proxy.width_m, proxy.height_m, proxy.depth_m);
  const outwardGap = Math.max(maxExtent * 0.08, 0.03);

  const frontDirection = axisVector(asset.front_axis).normalize();
  const frontOrigin = center.clone().add(
    frontDirection.clone().multiplyScalar(axisHalfExtent(asset.front_axis, proxy) + outwardGap),
  );
  addAxisArrowOverlay({
    origin: frontOrigin,
    axis: asset.front_axis,
    length: Math.max(maxExtent * 0.3, 0.12),
    color: 0xdc2626,
    label: "front",
  });

  const upDirection = axisVector(asset.up_axis).normalize();
  const upOrigin = center.clone().add(
    upDirection.clone().multiplyScalar(axisHalfExtent(asset.up_axis, proxy) + outwardGap),
  );
  addAxisArrowOverlay({
    origin: upOrigin,
    axis: asset.up_axis,
    length: Math.max(maxExtent * 0.24, 0.1),
    color: 0x2563eb,
    label: "up",
  });
}

function addLineSegment(points, color, opacity = 0.9) {
  const geometry = new THREE.BufferGeometry().setFromPoints(points);
  const material = new THREE.LineBasicMaterial({
    color,
    transparent: opacity < 1,
    opacity,
  });
  const line = new THREE.LineSegments(geometry, material);
  overlayRoot.add(line);
}

function addDimensionOverlay({
  start,
  end,
  outwardAxis,
  color,
  label,
  labelWidth = 0.28,
  labelHeight = 0.06,
}) {
  const direction = end.clone().sub(start);
  if (direction.lengthSq() < 1e-8) {
    return;
  }
  const outward = outwardAxis.clone().normalize();
  const tickLength = Math.max(direction.length() * 0.05, 0.03);
  const tickOffset = outward.clone().multiplyScalar(tickLength * 0.5);

  addLineSegment([start, end], color);
  addLineSegment([start.clone().sub(tickOffset), start.clone().add(tickOffset)], color, 0.8);
  addLineSegment([end.clone().sub(tickOffset), end.clone().add(tickOffset)], color, 0.8);

  const labelSprite = makeTextSprite(label, color, labelWidth, labelHeight);
  labelSprite.position.copy(
    start
      .clone()
      .add(end)
      .multiplyScalar(0.5)
      .add(outward.clone().multiplyScalar(tickLength * 1.6)),
  );
  overlayRoot.add(labelSprite);
}

function addBoundsDimensionOverlays(bounds) {
  if (!bounds) {
    return;
  }
  const minX = bounds.min_corner_m.x;
  const maxX = bounds.max_corner_m.x;
  const minY = bounds.min_corner_m.y;
  const maxY = bounds.max_corner_m.y;
  const minZ = bounds.min_corner_m.z;
  const maxZ = bounds.max_corner_m.z;
  const maxExtent = Math.max(bounds.width_m, bounds.height_m, bounds.depth_m);
  const gap = Math.max(maxExtent * 0.1, 0.06);
  const labelWidth = Math.min(Math.max(maxExtent * 0.22, 0.16), 0.3);
  const labelHeight = Math.min(Math.max(maxExtent * 0.05, 0.038), 0.065);

  addDimensionOverlay({
    start: new THREE.Vector3(minX, minY - gap, maxZ + gap),
    end: new THREE.Vector3(maxX, minY - gap, maxZ + gap),
    outwardAxis: new THREE.Vector3(0, -1, 0),
    color: 0x4b5563,
    label: `${bounds.width_m.toFixed(3)} m`,
    labelWidth,
    labelHeight,
  });

  addDimensionOverlay({
    start: new THREE.Vector3(maxX + gap, minY, maxZ + gap),
    end: new THREE.Vector3(maxX + gap, maxY, maxZ + gap),
    outwardAxis: new THREE.Vector3(1, 0, 0),
    color: 0x1d4ed8,
    label: `${bounds.height_m.toFixed(3)} m`,
    labelWidth,
    labelHeight,
  });

  addDimensionOverlay({
    start: new THREE.Vector3(maxX + gap, minY - gap * 0.35, minZ),
    end: new THREE.Vector3(maxX + gap, minY - gap * 0.35, maxZ),
    outwardAxis: new THREE.Vector3(1, 0, 0),
    color: 0x7c3aed,
    label: `${bounds.depth_m.toFixed(3)} m`,
    labelWidth,
    labelHeight,
  });
}

function updateViewerToggleLabels() {
  elements.toggleXRayButton.textContent = `Surface X-ray: ${state.surfaceXRay ? "On" : "Off"}`;
  elements.toggleLiftButton.textContent = `Visual Lift: ${state.visualLift ? "On" : "Off"}`;
}

function renderViewer() {
  const renderToken = ++state.renderToken;
  updateViewerToggleLabels();
  clearGroup(overlayRoot);
  if (!state.currentDetail || !state.workingAsset) {
    elements.viewerStatus.textContent = "Select an asset to inspect its candidate semantics.";
    return;
  }

  const bounds = state.currentDetail.canonical_bounds || state.currentDetail.proxy_bounds;
  if (bounds) {
    const proxyBox = new THREE.Mesh(
      new THREE.BoxGeometry(bounds.width_m, bounds.height_m, bounds.depth_m),
      new THREE.MeshStandardMaterial({
        color: 0xb7c9c4,
        transparent: true,
        opacity: 0.0,
        depthWrite: false,
        roughness: 0.9,
      }),
    );
    proxyBox.position.set(bounds.center_m.x, bounds.center_m.y, bounds.center_m.z);
    overlayRoot.add(proxyBox);
    const proxyEdges = new THREE.LineSegments(
      new THREE.EdgesGeometry(new THREE.BoxGeometry(bounds.width_m, bounds.height_m, bounds.depth_m)),
      new THREE.LineBasicMaterial({
        color: 0x8aa39f,
        transparent: true,
        opacity: 0.35,
      }),
    );
    proxyEdges.position.copy(proxyBox.position);
    overlayRoot.add(proxyEdges);
    addObjectAxisOverlays(bounds, state.workingAsset);
    addBoundsDimensionOverlays(bounds);
  }

  const bottom = state.workingAsset.bottom_support_plane;
  addPlaneOverlay({
    width: bottom.width_m,
    depth: bottom.depth_m,
    position: new THREE.Vector3(
      bottom.local_center_m.x,
      bottom.local_center_m.y,
      bottom.local_center_m.z,
    ),
    normalAxis: bottom.normal_axis,
    frontAxis: state.workingAsset.front_axis,
    color: 0x0c6c66,
    opacity: 0.28,
    labelText: "bottom",
    displayOffsetSign: -1,
  });

  const surfaces = state.workingAsset.support_surfaces_v1 || [];
  surfaces.forEach((surface, index) => {
    addPlaneOverlay({
      width: surface.width_m,
      depth: surface.depth_m,
      position: new THREE.Vector3(
        surface.local_center_m.x,
        surface.height_m,
        surface.local_center_m.z,
      ),
      normalAxis: surface.normal_axis,
      frontAxis: surface.front_axis,
      color: index % 2 === 0 ? 0xc76f38 : 0x8f3b2e,
      opacity: 0.18,
      labelText: surface.surface_id,
    });
  });

  const width = bounds?.width_m || 1.0;
  const height = bounds?.height_m || 1.0;
  const depth = bounds?.depth_m || 1.0;
  const radius = Math.max(width, height, depth) * 1.8;
  camera.position.set(radius, height + radius * 0.3, radius);
  controls.target.set(0, height * 0.45, 0);
  controls.update();

  const reviewMesh = state.currentDetail.source_refs.review_mesh;
  if (reviewMesh) {
    elements.viewerStatus.textContent = "Loading review mesh from the AI2-THOR grouped source asset...";
    loadReviewMeshGroup(reviewMesh)
      .then((group) => {
        if (renderToken !== state.renderToken) {
          return;
        }
        if (group) {
          alignReviewMeshToProxy(group, bounds);
          overlayRoot.add(group);
          elements.viewerStatus.textContent =
            "Showing the real review mesh together with support and bottom-plane overlays.";
        } else {
          elements.viewerStatus.textContent =
            "Review mesh selection could not be resolved, so Explorer v0 is showing proxy geometry and overlays.";
        }
      })
      .catch((error) => {
        if (renderToken !== state.renderToken) {
          return;
        }
        elements.viewerStatus.textContent = `Review mesh load failed, falling back to proxy geometry: ${error.message}`;
      });
    return;
  }

  const modelPack = state.currentDetail.source_refs.model_pack;
  elements.viewerStatus.textContent = modelPack
    ? "Explorer v0 is showing prefab-derived proxy geometry because no review-mesh selection was resolved for this asset."
    : "Explorer v0 is showing prefab-derived proxy geometry and overlays.";
}

function updateQuickReviewBadge() {
  if (!state.workingAsset) {
    elements.reviewBadge.textContent = "Auto / Unreviewed";
    return;
  }
  elements.reviewBadge.textContent = reviewStatusLabel(state.workingAsset);
}

function queueStatusLabel(asset) {
  const status = asset?.queue_status || "pending";
  if (status === "reviewed") {
    return "Queued: Accepted";
  }
  if (status === "needs_fix") {
    return "Queued: Needs Fix";
  }
  if (status === "rejected") {
    return "Queued: Rejected";
  }
  if (status === "in_progress") {
    return "Queued: In Progress";
  }
  if (status === "deferred") {
    return "Queued: Deferred";
  }
  return "Queued: Pending";
}

function reviewStatusLabel(asset) {
  const status = asset?.review_status || "auto";
  const needsFixCount = Array.isArray(asset?.needs_fix_targets_v0)
    ? asset.needs_fix_targets_v0.length
    : 0;
  if (status === "reviewed") {
    return "Accepted";
  }
  if (status === "rejected") {
    return "Rejected";
  }
  if (status === "uncertain") {
    return needsFixCount > 0 ? `Needs Fix · ${needsFixCount}` : "Needs Fix";
  }
  return "Auto / Unreviewed";
}

function ensureReviewScopeFields(asset) {
  if (!asset || typeof asset !== "object") {
    return;
  }
  asset.review_scope_v0 = [...REVIEW_SCOPE_TARGET_IDS_V0];
  if (!Array.isArray(asset.needs_fix_targets_v0)) {
    asset.needs_fix_targets_v0 = [];
  } else {
    asset.needs_fix_targets_v0 = asset.needs_fix_targets_v0.filter((target) =>
      REVIEW_SCOPE_TARGET_IDS_V0.includes(target),
    );
  }
}

function selectedNeedsFixTargetsFromUI() {
  return Array.from(
    elements.reviewScopeList.querySelectorAll('input[data-review-target]:checked'),
  ).map((input) => input.getAttribute("data-review-target"));
}

function syncReviewScopeFieldsFromUI() {
  if (!state.workingAsset) {
    return;
  }
  ensureReviewScopeFields(state.workingAsset);
  state.workingAsset.needs_fix_targets_v0 = selectedNeedsFixTargetsFromUI();
}

function renderReviewScope() {
  if (!state.workingAsset) {
    elements.reviewScopeList.innerHTML = "<p class=\"asset-subtext\">Select an asset to review its scope.</p>";
    return;
  }
  ensureReviewScopeFields(state.workingAsset);
  const selectedTargets = new Set(state.workingAsset.needs_fix_targets_v0);
  elements.reviewScopeList.innerHTML = REVIEW_SCOPE_ITEMS_V0.map(
    (item) => `
      <label class="review-scope-item">
        <input
          type="checkbox"
          data-review-target="${item.id}"
          ${selectedTargets.has(item.id) ? "checked" : ""}
        />
        <div>
          <strong>${item.label}</strong>
          <span>${item.description}</span>
        </div>
      </label>
    `,
  ).join("");

  elements.reviewScopeList.querySelectorAll("input[data-review-target]").forEach((input) => {
    input.addEventListener("change", () => {
      syncReviewScopeFieldsFromUI();
      updateQuickReviewBadge();
    });
  });
}

function loadReviewMeshAsset(url) {
  if (!reviewMeshCache.has(url)) {
    reviewMeshCache.set(url, fbxLoader.loadAsync(url));
  }
  return reviewMeshCache.get(url);
}

function makeReviewMaterial(color) {
  return new THREE.MeshStandardMaterial({
    color,
    transparent: state.surfaceXRay,
    opacity: state.surfaceXRay ? 0.28 : 1.0,
    depthWrite: !state.surfaceXRay,
    roughness: 0.82,
    metalness: 0.05,
    flatShading: false,
  });
}

function cloneReviewMeshObject(sourceObject, color) {
  const clone = sourceObject.clone(true);
  let added = 0;
  clone.traverse((child) => {
    if (!child.isMesh || !child.geometry) {
      return;
    }
    child.material = makeReviewMaterial(color);
    child.castShadow = false;
    child.receiveShadow = false;
    added += 1;
  });
  return added > 0 ? clone : null;
}

function normalizeMeshNodeName(name) {
  return String(name || "")
    .toLowerCase()
    .replace(/[^a-z0-9]/g, "");
}

function findReviewMeshNode(sourceScene, meshName) {
  const exact = sourceScene.getObjectByName(meshName);
  if (exact) {
    return exact;
  }
  const normalizedTarget = normalizeMeshNodeName(meshName);
  let match = null;
  sourceScene.traverse((node) => {
    if (match || !node.name) {
      return;
    }
    if (normalizeMeshNodeName(node.name) === normalizedTarget) {
      match = node;
    }
  });
  return match;
}

function alignReviewMeshToProxy(group, bounds) {
  if (!bounds) {
    return;
  }
  const rawBox = new THREE.Box3().setFromObject(group);
  if (rawBox.isEmpty()) {
    return;
  }
  const rawSize = new THREE.Vector3();
  rawBox.getSize(rawSize);
  const widthRatio = bounds.width_m / rawSize.x;
  const heightRatio = bounds.height_m / rawSize.y;
  const depthRatio = bounds.depth_m / rawSize.z;
  const ratios = [widthRatio, heightRatio, depthRatio].filter(
    (value) => Number.isFinite(value) && value > 0,
  );
  if (!ratios.length) {
    return;
  }
  let uniformScale = null;
  const horizontalRatios = [widthRatio, depthRatio].filter(
    (value) => Number.isFinite(value) && value > 0,
  );
  if (horizontalRatios.length === 2) {
    const horizontalSpread =
      Math.max(...horizontalRatios) / Math.min(...horizontalRatios);
    if (horizontalSpread <= 1.15) {
      uniformScale = (horizontalRatios[0] + horizontalRatios[1]) / 2;
    }
  }
  if (!uniformScale) {
    ratios.sort((a, b) => a - b);
    uniformScale = ratios[Math.floor(ratios.length / 2)];
  }
  group.scale.multiplyScalar(uniformScale);

  const fittedBox = new THREE.Box3().setFromObject(group);
  const fittedCenter = new THREE.Vector3();
  fittedBox.getCenter(fittedCenter);
  group.position.add(
    new THREE.Vector3(
      bounds.center_m.x - fittedCenter.x,
      0,
      bounds.center_m.z - fittedCenter.z,
    ),
  );
  const alignedBox = new THREE.Box3().setFromObject(group);
  group.position.add(
    new THREE.Vector3(
      0,
      bounds.min_corner_m.y - alignedBox.min.y,
      0,
    ),
  );
}

async function loadReviewMeshGroup(reviewMesh) {
  const sourceScene = await loadReviewMeshAsset(reviewMesh.url);
  const group = new THREE.Group();
  let added = 0;
  reviewMesh.mesh_instances.forEach((instance, index) => {
    const sourceNode = findReviewMeshNode(sourceScene, instance.mesh_name);
    if (!sourceNode) {
      return;
    }
    const clone = cloneReviewMeshObject(sourceNode, index % 2 === 0 ? 0xb9a175 : 0x8790a8);
    if (!clone) {
      return;
    }
    clone.position.set(
      instance.local_position_m.x,
      instance.local_position_m.y,
      instance.local_position_m.z,
    );
    clone.quaternion.set(
      instance.local_rotation_xyzw.x,
      instance.local_rotation_xyzw.y,
      instance.local_rotation_xyzw.z,
      instance.local_rotation_xyzw.w,
    );
    clone.scale.set(
      instance.local_scale.x,
      instance.local_scale.y,
      instance.local_scale.z,
    );
    clone.name = instance.mesh_name;
    group.add(clone);
    added += 1;
  });
  return added > 0 ? group : null;
}

function makeOptionList(options, currentValue) {
  return options
    .map(
      (value) => `<option value="${value}" ${value === currentValue ? "selected" : ""}>${value}</option>`,
    )
    .join("");
}

function numericField(name, label, value, step = "0.001") {
  return `
    <div class="field">
      <label for="${name}">${label}</label>
      <input id="${name}" name="${name}" type="number" step="${step}" value="${value}" />
    </div>
  `;
}

function textField(name, label, value) {
  return `
    <div class="field">
      <label for="${name}">${label}</label>
      <input id="${name}" name="${name}" type="text" value="${value ?? ""}" />
    </div>
  `;
}

function selectField(name, label, value, options) {
  return `
    <div class="field">
      <label for="${name}">${label}</label>
      <select id="${name}" name="${name}">
        ${makeOptionList(options, value)}
      </select>
    </div>
  `;
}

function renderDetailMeta() {
  if (!state.currentDetail) {
    elements.detailMeta.innerHTML = "<p>No asset selected yet.</p>";
    return;
  }

  const {
    asset,
    source_record: sourceRecord,
    current_source: currentSource,
    source_refs: refs,
    queue_entry: queueEntry,
    batch_summary: batchSummary,
    canonical_bounds: canonicalBounds,
    proxy_bounds: proxy,
  } =
    state.currentDetail;
  const bounds = canonicalBounds || proxy;
  const modelPackNote = refs.model_pack
    ? `<p><strong>Model pack:</strong> <a href="${refs.model_pack.url}" target="_blank" rel="noreferrer">${refs.model_pack.format}</a></p>`
    : "<p><strong>Model pack:</strong> unresolved</p>";
  const boundsSource = bounds.normalization_source || bounds.measurement_source || "unknown";
  const boundsLabel = canonicalBounds ? "Canonical bounds" : "Proxy bounds";

  elements.detailMeta.innerHTML = `
    <div>
      <strong>${sourceRecord.display_name || asset.asset_id}</strong>
      <p><strong>Role:</strong> ${asset.asset_role}</p>
      <p><strong>Category:</strong> ${asset.category}</p>
      <p><strong>Current source:</strong> ${currentSource}</p>
      ${
        queueEntry
          ? `<p><strong>Review batch:</strong> ${queueEntry.batch_title || queueEntry.batch_id}</p>`
          : ""
      }
    </div>
    <div class="inline-note">
      <p><strong>Prefab:</strong> <a href="${refs.prefab.url}" target="_blank" rel="noreferrer">source prefab</a></p>
      ${modelPackNote}
      <p><strong>${boundsLabel}:</strong> ${bounds.width_m.toFixed(3)} × ${bounds.height_m.toFixed(3)} × ${bounds.depth_m.toFixed(3)} m</p>
      <p><strong>Bounds source:</strong> ${boundsSource}</p>
      ${
        batchSummary
          ? `<p><strong>Batch progress:</strong> ${batchSummary.reviewed_count} accepted, ${batchSummary.needs_fix_count} needs fix, ${batchSummary.rejected_count} rejected, ${batchSummary.pending_count} pending</p>`
          : ""
      }
    </div>
  `;
}

function renderForm() {
  if (!state.workingAsset) {
    elements.editorForm.innerHTML = "";
    elements.saveButton.disabled = true;
    elements.resetAutoButton.disabled = true;
    elements.acceptButton.disabled = true;
    elements.needsFixButton.disabled = true;
    elements.rejectButton.disabled = true;
    elements.quickReviewNotes.value = "";
    renderReviewScope();
    updateQuickReviewBadge();
    return;
  }

  const asset = state.workingAsset;
  ensureReviewScopeFields(asset);
  elements.acceptButton.disabled = false;
  elements.needsFixButton.disabled = false;
  elements.rejectButton.disabled = false;
  elements.resetAutoButton.disabled = false;
  elements.quickReviewNotes.value = asset.review_notes || "";
  renderReviewScope();
  updateQuickReviewBadge();
  elements.toggleAdvancedButton.textContent = state.advancedVisible
    ? "Hide Advanced Edits"
    : "Show Advanced Edits";
  elements.editorForm.classList.toggle("is-hidden", !state.advancedVisible);
  const bottom = asset.bottom_support_plane;
  const supportsSurfaceGroups = (asset.support_surfaces_v1 || [])
    .map(
      (surface, index) => `
        <section class="surface-card" data-surface-index="${index}">
          <div class="field-grid">
            ${textField(`surface-id-${index}`, "Surface Id", surface.surface_id)}
            ${textField(`surface-type-${index}`, "Surface Type", surface.surface_type)}
            ${textField(`surface-class-${index}`, "Surface Class", surface.surface_class)}
            ${selectField(`surface-normal-${index}`, "Normal Axis", surface.normal_axis, AXIS_OPTIONS)}
            ${selectField(`surface-front-${index}`, "Front Axis", surface.front_axis, AXIS_OPTIONS)}
            ${selectField(`surface-review-${index}`, "Review Status", surface.review_status, REVIEW_STATUS_OPTIONS)}
            ${numericField(`surface-width-${index}`, "Width (m)", surface.width_m)}
            ${numericField(`surface-depth-${index}`, "Depth (m)", surface.depth_m)}
            ${numericField(`surface-height-${index}`, "Height (m)", surface.height_m)}
            ${numericField(`surface-center-x-${index}`, "Center X (m)", surface.local_center_m.x)}
            ${numericField(`surface-center-z-${index}`, "Center Z (m)", surface.local_center_m.z)}
            ${numericField(`surface-margin-${index}`, "Usable Margin (m)", surface.usable_margin_m)}
            ${textField(
              `surface-supports-${index}`,
              "Supports Categories",
              surface.supports_categories.join(", "),
            )}
            ${textField(`surface-placement-${index}`, "Placement Style", surface.placement_style)}
          </div>
        </section>
      `,
    )
    .join("");

  const childPlacement = asset.child_placement
    ? `
      <section class="field-group">
        <div>
          <strong>Child Placement</strong>
          <p>Parent surfaces stay read-only for child objects.</p>
        </div>
        <div class="field-grid">
          ${textField("child-base-shape", "Base Shape", asset.child_placement.base_shape)}
          ${selectField("child-upright-axis", "Upright Axis", asset.child_placement.upright_axis, AXIS_OPTIONS)}
          ${numericField("child-base-width", "Base Width (m)", asset.child_placement.base_width_m)}
          ${numericField("child-base-depth", "Base Depth (m)", asset.child_placement.base_depth_m)}
          ${numericField("child-support-margin", "Support Margin (m)", asset.child_placement.support_margin_m)}
          ${textField(
            "child-placement-style",
            "Placement Style",
            asset.child_placement.placement_style,
          )}
          <div class="field full">
            <label for="child-allowed-surfaces">Allowed Surface Types</label>
            <textarea id="child-allowed-surfaces">${asset.child_placement.allowed_surface_types.join(", ")}</textarea>
          </div>
          <div class="field">
            <label for="child-stable-support">Stable Support Required</label>
            <select id="child-stable-support">
              <option value="true" ${asset.child_placement.stable_support_required ? "selected" : ""}>true</option>
              <option value="false" ${asset.child_placement.stable_support_required ? "" : "selected"}>false</option>
            </select>
          </div>
        </div>
      </section>
    `
    : "";

  elements.editorForm.innerHTML = `
    <section class="field-group">
      <div>
        <strong>Object Semantics</strong>
        <p>These are the fields we expect reviewers to confirm first.</p>
      </div>
      <div class="field-grid">
        ${textField("category", "Category", asset.category)}
        ${textField("placement-class", "Placement Class", asset.placement_class)}
        ${selectField("front-axis", "Front Axis", asset.front_axis, AXIS_OPTIONS)}
        ${selectField("up-axis", "Up Axis", asset.up_axis, AXIS_OPTIONS)}
        ${selectField("review-status", "Review Status", asset.review_status, REVIEW_STATUS_OPTIONS)}
      </div>
    </section>
    <section class="field-group">
      <div>
        <strong>Bottom Support Plane</strong>
        <p>This plane is shown in teal in the viewer.</p>
      </div>
      <div class="field-grid">
        ${textField("bottom-shape", "Shape", bottom.shape)}
        ${selectField("bottom-normal-axis", "Normal Axis", bottom.normal_axis, AXIS_OPTIONS)}
        ${selectField("bottom-review-status", "Review Status", bottom.review_status, REVIEW_STATUS_OPTIONS)}
        ${numericField("bottom-width", "Width (m)", bottom.width_m)}
        ${numericField("bottom-depth", "Depth (m)", bottom.depth_m)}
        ${numericField("bottom-center-x", "Center X (m)", bottom.local_center_m.x)}
        ${numericField("bottom-center-y", "Center Y (m)", bottom.local_center_m.y)}
        ${numericField("bottom-center-z", "Center Z (m)", bottom.local_center_m.z)}
      </div>
    </section>
    ${
      asset.asset_role === "parent_object"
        ? `
          <section class="field-group">
            <div>
              <strong>Parent Support Surfaces</strong>
              <p>Explorer v0 keeps these as rectangle-only reviews.</p>
            </div>
            <div class="field">
              <label for="supports-objects">Supports Objects</label>
              <select id="supports-objects">
                <option value="true" ${asset.supports_objects ? "selected" : ""}>true</option>
                <option value="false" ${asset.supports_objects ? "" : "selected"}>false</option>
              </select>
            </div>
            ${supportsSurfaceGroups}
          </section>
        `
        : ""
    }
    ${childPlacement}
  `;

  elements.saveButton.disabled = false;
}

function parseNumber(id) {
  return Number(document.getElementById(id).value);
}

function updateAssetFromForm() {
  if (!state.workingAsset) {
    return;
  }
  const asset = state.workingAsset;
  ensureReviewScopeFields(asset);
  asset.category = document.getElementById("category").value.trim();
  asset.placement_class = document.getElementById("placement-class").value.trim();
  asset.front_axis = document.getElementById("front-axis").value;
  asset.up_axis = document.getElementById("up-axis").value;
  asset.review_status = document.getElementById("review-status").value;
  asset.review_notes = elements.quickReviewNotes.value;

  asset.bottom_support_plane.shape = document.getElementById("bottom-shape").value.trim();
  asset.bottom_support_plane.normal_axis = document.getElementById("bottom-normal-axis").value;
  asset.bottom_support_plane.review_status = document.getElementById("bottom-review-status").value;
  asset.bottom_support_plane.width_m = parseNumber("bottom-width");
  asset.bottom_support_plane.depth_m = parseNumber("bottom-depth");
  asset.bottom_support_plane.local_center_m.x = parseNumber("bottom-center-x");
  asset.bottom_support_plane.local_center_m.y = parseNumber("bottom-center-y");
  asset.bottom_support_plane.local_center_m.z = parseNumber("bottom-center-z");

  if (asset.asset_role === "parent_object") {
    asset.supports_objects = document.getElementById("supports-objects").value === "true";
    asset.support_surfaces_v1.forEach((surface, index) => {
      surface.surface_id = document.getElementById(`surface-id-${index}`).value.trim();
      surface.surface_type = document.getElementById(`surface-type-${index}`).value.trim();
      surface.surface_class = document.getElementById(`surface-class-${index}`).value.trim();
      surface.normal_axis = document.getElementById(`surface-normal-${index}`).value;
      surface.front_axis = document.getElementById(`surface-front-${index}`).value;
      surface.review_status = document.getElementById(`surface-review-${index}`).value;
      surface.width_m = parseNumber(`surface-width-${index}`);
      surface.depth_m = parseNumber(`surface-depth-${index}`);
      surface.height_m = parseNumber(`surface-height-${index}`);
      surface.local_center_m.x = parseNumber(`surface-center-x-${index}`);
      surface.local_center_m.z = parseNumber(`surface-center-z-${index}`);
      surface.local_center_m.y = surface.height_m;
      surface.usable_margin_m = parseNumber(`surface-margin-${index}`);
      surface.supports_categories = document
        .getElementById(`surface-supports-${index}`)
        .value.split(",")
        .map((value) => value.trim())
        .filter(Boolean);
      surface.placement_style = document.getElementById(`surface-placement-${index}`).value.trim();
    });
  }

  if (asset.asset_role === "child_object" && asset.child_placement) {
    asset.child_placement.base_shape = document.getElementById("child-base-shape").value.trim();
    asset.child_placement.upright_axis = document.getElementById("child-upright-axis").value;
    asset.child_placement.base_width_m = parseNumber("child-base-width");
    asset.child_placement.base_depth_m = parseNumber("child-base-depth");
    asset.child_placement.support_margin_m = parseNumber("child-support-margin");
    asset.child_placement.placement_style = document.getElementById("child-placement-style").value.trim();
    asset.child_placement.allowed_surface_types = document
      .getElementById("child-allowed-surfaces")
      .value.split(",")
      .map((value) => value.trim())
      .filter(Boolean);
    asset.child_placement.stable_support_required =
      document.getElementById("child-stable-support").value === "true";
  }

  syncReviewScopeFieldsFromUI();
  if (asset.review_status !== "uncertain") {
    asset.needs_fix_targets_v0 = [];
  }

  renderViewer();
  updateQuickReviewBadge();
}

function setNestedReviewStatus(value, node = state.workingAsset) {
  if (!node || typeof node !== "object") {
    return;
  }
  if (Object.prototype.hasOwnProperty.call(node, "review_status")) {
    node.review_status = value;
  }
  if (Array.isArray(node)) {
    node.forEach((item) => setNestedReviewStatus(value, item));
    return;
  }
  Object.values(node).forEach((child) => {
    if (child && typeof child === "object") {
      setNestedReviewStatus(value, child);
    }
  });
}

async function saveCurrentAsset() {
  if (!state.currentAssetId || !state.workingAsset) {
    return;
  }
  const savedAssetId = state.currentAssetId;
  const detail = await fetchJson(`/api/object-semantics/assets/${state.currentAssetId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(state.workingAsset),
  });
  state.currentDetail = detail;
  state.workingAsset = structuredClone(detail.asset);
  elements.assetSubtitle.textContent = buildAssetSubtitle(detail);
  await loadAssets({ preserveSelection: false });
  return savedAssetId;
}

async function applyQuickReview(status) {
  if (!state.workingAsset) {
    return;
  }
  ensureReviewScopeFields(state.workingAsset);
  if (state.advancedVisible) {
    updateAssetFromForm();
  } else {
    state.workingAsset.review_notes = elements.quickReviewNotes.value;
    syncReviewScopeFieldsFromUI();
  }
  if (status === "reviewed") {
    setNestedReviewStatus("reviewed");
    state.workingAsset.needs_fix_targets_v0 = [];
  } else if (status === "uncertain") {
    if (state.workingAsset.needs_fix_targets_v0.length === 0) {
      window.alert("Select at least one review-scope item before marking this asset as Needs Fix.");
      return;
    }
    state.workingAsset.review_status = "uncertain";
  } else if (status === "rejected") {
    state.workingAsset.review_status = "rejected";
    state.workingAsset.needs_fix_targets_v0 = [];
  } else if (status === "auto") {
    setNestedReviewStatus("auto");
    state.workingAsset.needs_fix_targets_v0 = [];
  }
  updateQuickReviewBadge();
  const nextAssetId = nextReviewTargetIdAfter(state.currentAssetId);
  const button =
    status === "auto"
      ? elements.resetAutoButton
      : status === "reviewed"
      ? elements.acceptButton
      : status === "uncertain"
        ? elements.needsFixButton
        : elements.rejectButton;
  const originalLabel = button.textContent;
  button.disabled = true;
  button.textContent = "Saving...";
  try {
    await saveCurrentAsset();
    if (nextAssetId && nextAssetId !== state.currentAssetId) {
      await loadAsset(nextAssetId);
    } else if (state.currentAssetId) {
      await loadAsset(state.currentAssetId);
    }
  } catch (error) {
    window.alert(`Save failed: ${error.message}`);
  } finally {
    button.disabled = false;
    button.textContent = originalLabel;
  }
}

function renderQueueSummary() {
  if (!state.reviewQueue || !Array.isArray(state.reviewQueue.batches)) {
    elements.queueSummary.innerHTML = "";
    return;
  }
  const reviewedCount = state.reviewQueue.batches.reduce((sum, batch) => sum + (batch.reviewed_count || 0), 0);
  const needsFixCount = state.reviewQueue.batches.reduce((sum, batch) => sum + (batch.needs_fix_count || 0), 0);
  const rejectedCount = state.reviewQueue.batches.reduce((sum, batch) => sum + (batch.rejected_count || 0), 0);
  const pendingCount = state.reviewQueue.batches.reduce((sum, batch) => sum + (batch.pending_count || 0), 0);
  elements.queueSummary.innerHTML = `
    <div class="queue-summary-card">
      <strong>Review Queue</strong>
      <p>${state.reviewQueue.batch_count} batches · ${state.reviewQueue.item_count} assets</p>
      <div class="queue-summary-metrics">
        <span>Accepted ${reviewedCount}</span>
        <span>Needs Fix ${needsFixCount}</span>
        <span>Rejected ${rejectedCount}</span>
        <span>Pending ${pendingCount}</span>
      </div>
    </div>
  `;
}

function renderAssetList() {
  const groupedAssets = new Map();
  state.assets.forEach((asset) => {
    const key = asset.batch_id || "__ungrouped__";
    if (!groupedAssets.has(key)) {
      groupedAssets.set(key, []);
    }
    groupedAssets.get(key).push(asset);
  });

  const batchById = new Map((state.reviewQueue?.batches || []).map((batch) => [batch.batch_id, batch]));
  const sections = [];
  groupedAssets.forEach((assets, batchId) => {
    const batch = batchById.get(batchId);
    const header = batch
      ? `
        <div class="asset-batch-header">
          <div>
            <strong>${batch.title}</strong>
            <p>${batch.asset_count} assets · session target ${batch.recommended_session_asset_count}</p>
          </div>
          <div class="status-chip">Accepted ${batch.reviewed_count} · Pending ${batch.pending_count}</div>
        </div>
      `
      : "";
    const cards = assets
      .map(
        (asset) => `
          <button class="asset-card asset-card--${asset.review_status} ${asset.asset_id === state.currentAssetId ? "active" : ""}" data-asset-id="${asset.asset_id}">
            <div class="asset-card-header">
              <strong>${asset.display_name}</strong>
              ${
                asset.review_status === "reviewed"
                  ? '<span class="asset-card-mark" aria-label="Reviewed">Accepted</span>'
                  : asset.review_status === "uncertain"
                    ? '<span class="asset-card-mark asset-card-mark--needs-fix" aria-label="Needs Fix">Needs Fix</span>'
                    : asset.review_status === "rejected"
                      ? '<span class="asset-card-mark asset-card-mark--rejected" aria-label="Rejected">Rejected</span>'
                      : ""
              }
            </div>
            <div class="asset-subtext">${asset.asset_role} · ${asset.category}</div>
            <div class="status-chip">${queueStatusLabel(asset)}${asset.has_reviewed_override ? " · reviewed copy" : ""}</div>
          </button>
        `,
      )
      .join("");
    sections.push(`<section class="asset-batch">${header}<div class="asset-batch-list">${cards}</div></section>`);
  });
  elements.assetList.innerHTML = sections.join("");

  elements.assetList.querySelectorAll("[data-asset-id]").forEach((button) => {
    button.addEventListener("click", () => {
      loadAsset(button.getAttribute("data-asset-id"));
    });
  });
}

function buildAssetSubtitle(detail) {
  const parts = [
    `${detail.asset.asset_role}`,
    `${detail.asset.category}`,
    `${detail.current_source}`,
  ];
  if (detail.queue_entry?.batch_title) {
    parts.push(detail.queue_entry.batch_title);
  }
  return parts.join(" · ");
}

async function loadAssets({ preserveSelection = true } = {}) {
  const payload = await fetchJson("/api/object-semantics/assets");
  state.assets = payload.assets;
  state.reviewQueue = payload.review_queue || null;
  renderQueueSummary();
  renderAssetList();
  if (!preserveSelection) {
    return;
  }
  if (state.assets.length && !state.currentAssetId) {
    await loadAsset(state.assets[0].asset_id);
  }
}

async function loadAsset(assetId) {
  state.currentAssetId = assetId;
  const detail = await fetchJson(`/api/object-semantics/assets/${assetId}`);
  state.currentDetail = detail;
  state.workingAsset = structuredClone(detail.asset);
  renderAssetList();
  renderDetailMeta();
  renderForm();
  renderViewer();
  elements.assetTitle.textContent = detail.source_record.display_name || assetId;
  elements.assetSubtitle.textContent = buildAssetSubtitle(detail);
}

function navigateAssetByOffset(offset) {
  if (!state.assets.length || !state.currentAssetId) {
    return;
  }
  const currentIndex = state.assets.findIndex((asset) => asset.asset_id === state.currentAssetId);
  if (currentIndex < 0) {
    return;
  }
  const nextIndex = currentIndex + offset;
  if (nextIndex < 0 || nextIndex >= state.assets.length) {
    return;
  }
  loadAsset(state.assets[nextIndex].asset_id);
}

function nextReviewTargetIdAfter(assetId) {
  if (!state.assets.length || !assetId) {
    return null;
  }
  const currentIndex = state.assets.findIndex((asset) => asset.asset_id === assetId);
  if (currentIndex < 0) {
    return null;
  }
  const currentAsset = state.assets[currentIndex];
  const currentBatchId = currentAsset.batch_id;
  for (let index = currentIndex + 1; index < state.assets.length; index += 1) {
    const asset = state.assets[index];
    if (asset.batch_id === currentBatchId && asset.queue_status === "pending") {
      return asset.asset_id;
    }
  }
  for (let index = currentIndex + 1; index < state.assets.length; index += 1) {
    const asset = state.assets[index];
    if (asset.queue_status === "pending" || asset.queue_status === "needs_fix") {
      return asset.asset_id;
    }
  }
  if (currentIndex + 1 < state.assets.length) {
    return state.assets[currentIndex + 1].asset_id;
  }
  return assetId;
}

function isTypingTarget(target) {
  if (!target || !(target instanceof HTMLElement)) {
    return false;
  }
  const tagName = target.tagName.toLowerCase();
  return (
    tagName === "input" ||
    tagName === "textarea" ||
    tagName === "select" ||
    target.isContentEditable
  );
}

elements.editorForm.addEventListener("input", updateAssetFromForm);
elements.quickReviewNotes.addEventListener("input", () => {
  if (state.workingAsset) {
    state.workingAsset.review_notes = elements.quickReviewNotes.value;
  }
});
elements.toggleAdvancedButton.addEventListener("click", () => {
  state.advancedVisible = !state.advancedVisible;
  renderForm();
});
elements.toggleXRayButton.addEventListener("click", () => {
  state.surfaceXRay = !state.surfaceXRay;
  renderViewer();
});
elements.toggleLiftButton.addEventListener("click", () => {
  state.visualLift = !state.visualLift;
  renderViewer();
});
elements.acceptButton.addEventListener("click", async () => {
  await applyQuickReview("reviewed");
});
elements.resetAutoButton.addEventListener("click", async () => {
  await applyQuickReview("auto");
});
elements.needsFixButton.addEventListener("click", async () => {
  await applyQuickReview("uncertain");
});
elements.rejectButton.addEventListener("click", async () => {
  await applyQuickReview("rejected");
});
elements.saveButton.addEventListener("click", async () => {
  if (!state.currentAssetId || !state.workingAsset) {
    return;
  }
  updateAssetFromForm();
  if (
    state.workingAsset.review_status === "uncertain" &&
    state.workingAsset.needs_fix_targets_v0.length === 0
  ) {
    window.alert("Select at least one review-scope item before saving an asset marked Needs Fix.");
    return;
  }
  elements.saveButton.disabled = true;
  elements.saveButton.textContent = "Saving...";
  try {
    await saveCurrentAsset();
    await loadAsset(state.currentAssetId);
  } catch (error) {
    window.alert(`Save failed: ${error.message}`);
  } finally {
    elements.saveButton.disabled = false;
    elements.saveButton.textContent = "Save Advanced Edits";
  }
});
window.addEventListener("keydown", (event) => {
  if (event.defaultPrevented || event.altKey || event.ctrlKey || event.metaKey) {
    return;
  }
  if (isTypingTarget(event.target)) {
    return;
  }
  if (event.key === "ArrowRight" || event.key === "ArrowDown" || event.key === "j" || event.key === "J") {
    event.preventDefault();
    navigateAssetByOffset(1);
    return;
  }
  if (event.key === "ArrowLeft" || event.key === "ArrowUp" || event.key === "k" || event.key === "K") {
    event.preventDefault();
    navigateAssetByOffset(-1);
  }
});

loadAssets().catch((error) => {
  elements.viewerStatus.textContent = `Explorer load failed: ${error.message}`;
});
