/** Class implementing 3D terrain. */
class Terrain {
  /**
   * Initialize members of a Terrain object
   * @param {number} div Number of triangles along x axis and y axis
   * @param {number} minX Minimum X coordinate value
   * @param {number} maxX Maximum X coordinate value
   * @param {number} minY Minimum Y coordinate value
   * @param {number} maxY Maximum Y coordinate value
   */
  constructor(div,minX,maxX,minY,maxY) {
    this.div = div;
    this.minX=minX;
    this.minY=minY;
    this.maxX=maxX;
    this.maxY=maxY;
    this.minZ = 0.0;
    this.maxZ = 0.0;

    // Allocate vertex array
    this.vBuffer = [];
    // Allocate triangle array
    this.fBuffer = [];
    // Allocate normal array
    this.nBuffer = [];
    // Allocate array for edges so we can draw wireframe
    this.eBuffer = [];
    console.log("Terrain: Allocated buffers");

    this.generateTriangles();
    console.log("Terrain: Generated triangles");

    this.generateLines();
    console.log("Terrain: Generated lines");

    // Get extension for 4 byte integer indices for drwElements
    var ext = gl.getExtension('OES_element_index_uint');
    if (ext == null) {
      alert("OES_element_index_uint is unsupported by your browser and terrain generation cannot proceed.");
    }
  }

  /**
   * Return the x,y,z coordinates of a vertex at location (i,j)
   * @param {Object} v an an array of length 3 holding x,y,z coordinates
   * @param {number} i the ith row of vertices
   * @param {number} j the jth column of vertices
   */
  getVertex(v,i,j) {
    let vid = 3*(i*(this.div + 1) + j)
    v[0] = this.vBuffer[vid]
    v[1] = this.vBuffer[vid+1]
    v[2] = this.vBuffer[vid+2]
  }

  /**
   * Send the buffer objects to WebGL for rendering
   */
  loadBuffers() {
    // Specify the vertex coordinates
    this.VertexPositionBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, this.VertexPositionBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(this.vBuffer), gl.STATIC_DRAW);
    this.VertexPositionBuffer.itemSize = 3;
    this.VertexPositionBuffer.numItems = this.numVertices;
    console.log("Loaded ", this.VertexPositionBuffer.numItems, " vertices");

    // Specify normals to be able to do lighting calculations
    this.VertexNormalBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, this.VertexNormalBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(this.nBuffer),
      gl.STATIC_DRAW);
    this.VertexNormalBuffer.itemSize = 3;
    this.VertexNormalBuffer.numItems = this.numVertices;
    console.log("Loaded ", this.VertexNormalBuffer.numItems, " normals");

    // Specify faces of the terrain
    this.IndexTriBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, this.IndexTriBuffer);
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, new Uint32Array(this.fBuffer),
      gl.STATIC_DRAW);
    this.IndexTriBuffer.itemSize = 1;
    this.IndexTriBuffer.numItems = this.fBuffer.length;
    console.log("Loaded ", this.IndexTriBuffer.numItems, " triangles");

    //Setup Edges
    this.IndexEdgeBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, this.IndexEdgeBuffer);
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, new Uint32Array(this.eBuffer),
      gl.STATIC_DRAW);
    this.IndexEdgeBuffer.itemSize = 1;
    this.IndexEdgeBuffer.numItems = this.eBuffer.length;

    console.log("triangulatedPlane: loadBuffers");
  }

  /**
   * Render the triangles
   */
  drawTriangles() {
    gl.bindBuffer(gl.ARRAY_BUFFER, this.VertexPositionBuffer);
    gl.vertexAttribPointer(shaderProgram.vertexPositionAttribute, this.VertexPositionBuffer.itemSize,
      gl.FLOAT, false, 0, 0);

    // Bind normal buffer
    gl.bindBuffer(gl.ARRAY_BUFFER, this.VertexNormalBuffer);
    gl.vertexAttribPointer(shaderProgram.vertexNormalAttribute,
      this.VertexNormalBuffer.itemSize,
      gl.FLOAT, false, 0, 0);

    //Draw
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, this.IndexTriBuffer);
    gl.drawElements(gl.TRIANGLES, this.IndexTriBuffer.numItems, gl.UNSIGNED_INT,0);
  }

  /**
   * Render the triangle edges wireframe style
   */
  drawEdges() {
    gl.bindBuffer(gl.ARRAY_BUFFER, this.VertexPositionBuffer);
    gl.vertexAttribPointer(shaderProgram.vertexPositionAttribute, this.VertexPositionBuffer.itemSize,
      gl.FLOAT, false, 0, 0);

    // Bind normal buffer
    gl.bindBuffer(gl.ARRAY_BUFFER, this.VertexNormalBuffer);
    gl.vertexAttribPointer(shaderProgram.vertexNormalAttribute,
      this.VertexNormalBuffer.itemSize,
      gl.FLOAT, false, 0, 0);

    //Draw
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, this.IndexEdgeBuffer);
    gl.drawElements(gl.LINES, this.IndexEdgeBuffer.numItems, gl.UNSIGNED_INT,0);
  }
  /**
   * Fill the vertex and  triangle arrays
   */
  generateTriangles() {
    let deltaX = (this.maxX - this.minX) / this.div;
    let deltaY = (this.maxY - this.minY) / this.div;
    for (let i = 0; i <= this.div; ++i) {
      for (let j = 0; j <= this.div; ++j) {
        let x = this.minX + deltaX * j;
        let y = this.minY + deltaY * i;
        this.vBuffer.push(x);
        this.vBuffer.push(y);
        this.vBuffer.push(0);
      }
    }

    for (let i = 0; i < this.div; ++i) {
      for (let j = 0; j < this.div; ++j) {
        let bottomLeft = i * (this.div + 1) + j;

        // tri 1
        this.fBuffer.push(bottomLeft)
        this.fBuffer.push(bottomLeft + 1)
        this.fBuffer.push(bottomLeft + (this.div + 1))

        // tri 2
        this.fBuffer.push(bottomLeft + 1)
        this.fBuffer.push(bottomLeft + (this.div + 1))
        this.fBuffer.push(bottomLeft + (this.div + 1) + 1)
      }
    }

    // fault lines
    this.faultLines()

    // compute normals
    this.computeNormals()

    //
    this.numVertices = this.vBuffer.length/3;
    this.numFaces = this.fBuffer.length/3;
  }

  /**
   * Generate random fault lines to create semi-random terrain.
   * Every fault line partitions the plane, and we change the elevation of
   * every vertex on each side of the fault line.
   * Also calculates min and max elevation of the given points to pass to the shader
   * to create an elevation color-map.
   */
  faultLines() {
    const minLatitude = Math.min(...(latitude))
    const maxLatitude = Math.max(...(latitude))
    const minLongitude = Math.min(...(longitude))
    const maxLongitude = Math.max(...(longitude))
    const minElevation = Math.min(...(elevation))
    const maxElevation = Math.max(...(elevation))
    for (let i = 0; i < latitude.length; i++) {
      let y = ((latitude[i] - minLatitude) /
        (maxLatitude - minLatitude)) *
        ((this.div+1) * 0.8) + ((this.div+1) * 0.1)
      let x = ((longitude[i] - minLongitude) /
        (maxLongitude - minLongitude)) *
        ((this.div+1) * 0.8) + ((this.div+1) * 0.1)
      let elev = (0.09 * (elevation[i] - minElevation)
        / (maxElevation - minElevation)) + 0.02;

      let idx = Math.round(y) * (this.div+1) + Math.round(x);
      this.maxZ = Math.max(this.maxZ, elev)
      this.vBuffer[3*idx+2] = elev;
    }
  }

  /**
   * Compute per-vertex normals by computing the average of normal vectors of
   * all faces adjacent to a vertex.
   */
  computeNormals() {
    for (let i = 0; i <= this.div; ++i) {
      for (let j = 0; j <= this.div; ++j) {
        let self = [0, 0, 0]
        this.getVertex(self, i, j)
        let acc = glMatrix.vec3.create()

        if (j > 0 && i < this.div) {
          let below1 = [0, 0, 0]; this.getVertex(below1, i, j - 1)
          let v1 = glMatrix.vec3.fromValues(below1[0] - self[0], below1[1] - self[1], below1[2] - self[2])
          let below2 = [0, 0, 0]; this.getVertex(below2, i + 1, j - 1)
          let v2 = glMatrix.vec3.fromValues(below2[0] - self[0], below2[1] - self[1], below2[2] - self[2])
          let cross = glMatrix.vec3.create()
          glMatrix.vec3.cross(cross, v1, v2)
          if (glMatrix.vec3.dot(cross, glMatrix.vec3.fromValues(0, 0, 1)) < 0)
            glMatrix.vec3.negate(cross, cross)
          glMatrix.vec3.add(acc, acc, cross)

        }

        if (j > 0 && i < this.div) {
          let below2 = [0, 0, 0]; this.getVertex(below2, i + 1, j - 1)
          let v2 = glMatrix.vec3.fromValues(below2[0] - self[0], below2[1] - self[1], below2[2] - self[2])

          let right = [0, 0, 0]; this.getVertex(right, i + 1, j)
          let v3 = glMatrix.vec3.fromValues(right[0] - self[0], right[1] - self[1], right[2] - self[2])
          let cross = glMatrix.vec3.create()
          glMatrix.vec3.cross(cross, v2, v3)
          if (glMatrix.vec3.dot(cross, glMatrix.vec3.fromValues(0, 0, 1)) < 0)
            glMatrix.vec3.negate(cross, cross)
          glMatrix.vec3.add(acc, acc, cross)
        }

        if (i < this.div && j < this.div) {
          let right = [0, 0, 0]; this.getVertex(right, i + 1, j)
          let v1 = glMatrix.vec3.fromValues(right[0] - self[0], right[1] - self[1], right[2] - self[2])
          let top = [0, 0, 0]; this.getVertex(top, i, j + 1)
          let v2 = glMatrix.vec3.fromValues(top[0] - self[0], top[1] - self[1], top[2] - self[2])
          let cross = glMatrix.vec3.create()
          glMatrix.vec3.cross(cross, v1, v2)
          if (glMatrix.vec3.dot(cross, glMatrix.vec3.fromValues(0, 0, 1)) < 0)
            glMatrix.vec3.negate(cross, cross)
          glMatrix.vec3.add(acc, acc, cross)
        }

        if (i > 0 && j < this.div) {
          let top1 = [0, 0, 0]; this.getVertex(top1, i - 1, j + 1)
          let v1 = glMatrix.vec3.fromValues(top1[0] - self[0], top1[1] - self[1], top1[2] - self[2])
          let top2 = [0, 0, 0]; this.getVertex(top2, i, j + 1)
          let v2 = glMatrix.vec3.fromValues(top2[0] - self[0], top2[1] - self[1], top2[2] - self[2])
          let cross = glMatrix.vec3.create()
          glMatrix.vec3.cross(cross, v1, v2)
          if (glMatrix.vec3.dot(cross, glMatrix.vec3.fromValues(0, 0, 1)) < 0)
            glMatrix.vec3.negate(cross, cross)
          glMatrix.vec3.add(acc, acc, cross)
        }

        if (i > 0 && j < this.div) {
          let top1 = [0, 0, 0]; this.getVertex(top1, i - 1, j + 1)
          let v1 = glMatrix.vec3.fromValues(top1[0] - self[0], top1[1] - self[1], top1[2] - self[2])
          let top2 = [0, 0, 0]; this.getVertex(top2, i - 1, j)
          let v2 = glMatrix.vec3.fromValues(top2[0] - self[0], top2[1] - self[1], top2[2] - self[2])
          let cross = glMatrix.vec3.create()
          glMatrix.vec3.cross(cross, v1, v2)
          if (glMatrix.vec3.dot(cross, glMatrix.vec3.fromValues(0, 0, 1)) < 0)
            glMatrix.vec3.negate(cross, cross)
          glMatrix.vec3.add(acc, acc, cross)
        }

        if (i > 0 && j > 0) {
          let top1 = [0, 0, 0]; this.getVertex(top1, i - 1, j)
          let v1 = glMatrix.vec3.fromValues(top1[0] - self[0], top1[1] - self[1], top1[2] - self[2])
          let top2 = [0, 0, 0]; this.getVertex(top2, i, j - 1)
          let v2 = glMatrix.vec3.fromValues(top2[0] - self[0], top2[1] - self[1], top2[2] - self[2])
          let cross = glMatrix.vec3.create()
          glMatrix.vec3.cross(cross, v1, v2)
          if (glMatrix.vec3.dot(cross, glMatrix.vec3.fromValues(0, 0, 1)) < 0)
            glMatrix.vec3.negate(cross, cross)
          glMatrix.vec3.add(acc, acc, cross)
        }

        glMatrix.vec3.normalize(acc, acc)

        this.nBuffer.push(acc[0])
        this.nBuffer.push(acc[1])
        this.nBuffer.push(acc[2])
      }
    }
  }

  /**
   * Print vertices and triangles to console for debugging
   */
  printBuffers() {

    for(var i=0;i<this.numVertices;i++) {
      console.log("v ", this.vBuffer[i*3], " ",
        this.vBuffer[i*3 + 1], " ",
        this.vBuffer[i*3 + 2], " ");

    }

    for(var i=0;i<this.numFaces;i++) {
      console.log("f ", this.fBuffer[i*3], " ",
        this.fBuffer[i*3 + 1], " ",
        this.fBuffer[i*3 + 2], " ");

    }

  }

  /**
   * Generates line values from faces in faceArray
   * to enable wireframe rendering
   */
  generateLines() {
    var numTris=this.fBuffer.length/3;
    for (var f=0;f<numTris;f++) {
      var fid=f*3;
      this.eBuffer.push(this.fBuffer[fid]);
      this.eBuffer.push(this.fBuffer[fid+1]);

      this.eBuffer.push(this.fBuffer[fid+1]);
      this.eBuffer.push(this.fBuffer[fid+2]);

      this.eBuffer.push(this.fBuffer[fid+2]);
      this.eBuffer.push(this.fBuffer[fid]);
    }
  }
}
