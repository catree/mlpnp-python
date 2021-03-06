### IMPORTS
import numpy as np
import numpy.linalg as npl
import random
from scipy.linalg import null_space
import math
from math import sin, cos, acos, sqrt, pi
import time
import cv2

### RODRIGUES CONVERSIONS
def rod2rot(rod):
    phi = ((np.linalg.norm(rod) +pi) % (2*pi)) - pi # ensure that phi is in [-pi,pi]
    if phi > np.finfo(float).eps:
        N = np.matrix([ [0.     , -rod[2,0],  rod[1,0] ],
                        [rod[2,0] , 0.     , -rod[0,0] ],
                        [-rod[1,0], rod[0,0] , 0.      ] ])
        N = N / phi
        rot = np.identity(3) + (1-cos(phi))*(N**2) + sin(phi)*N
    else: rot = np.identity(3)
    return np.matrix(rot) #np.around(rot,6))

def rot2rod(rot):
    N = [0,0,0]
    phi = acos(max(min((np.trace(rot)-1)/2,1),-1))  # ensure that cos is in [-1,1] after rounds
    if phi > np.finfo(float).eps:
        sc = 1 / (2*sin(phi))
        N[0] = (rot[2,1] - rot[1,2])*sc
        N[1] = (rot[0,2] - rot[2,0])*sc
        N[2] = (rot[1,0] - rot[0,1])*sc
    norm = npl.norm(N)
    N = np.matrix(N)/norm*phi
    return N.transpose() #np.around(N,6)


### MLPNP REFINING
# MLPnP Jacobian
# Compute the jacobian in point pt of the residual function (eq.10 in paper)
def jacobian(pt, nullspace_r, nullspace_s, rot, trans):
    jac = np.zeros((2,6))

    r1 = nullspace_r[0]
    r2 = nullspace_r[1]
    r3 = nullspace_r[2]

    s1 = nullspace_s[0]
    s2 = nullspace_s[1]
    s3 = nullspace_s[2]

    X1 = pt[0]
    Y1 = pt[1]
    Z1 = pt[2]

    w1 = rot[0,0]
    w2 = rot[1,0]
    w3 = rot[2,0]
    t1 = trans[0]
    t2 = trans[1]
    t3 = trans[2]

    t5 = w1*w1
    t6 = w2*w2
    t7 = w3*w3
    t8 = t5+t6+t7 # phi**2
    t9 = sqrt(t8) # phi
    t10 = sin(t9)
    t11 = 1.0/sqrt(t8)
    t12 = cos(t9)
    t13 = t12-1.0
    t14 = 1.0/t8
    t16 = t10*t11*w3
    t17 = t13*t14*w1*w2
    t19 = t10*t11*w2
    t20 = t13*t14*w1*w3
    t24 = t6+t7
    t27 = t16+t17 # R12
    t28 = Y1*t27
    t29 = t19-t20 # R13
    t30 = Z1*t29
    t31 = t13*t14*t24
    t32 = t31+1.0 # R11
    t33 = X1*t32
    t15 = t1-t28+t30+t33
    t21 = t10*t11*w1
    t22 = t13*t14*w2*w3
    t45 = t5+t7
    t53 = t16-t17 # R21
    t54 = X1*t53
    t55 = t21+t22 # R23
    t56 = Z1*t55
    t57 = t13*t14*t45
    t58 = t57+1.0 # R22
    t59 = Y1*t58
    t18 = t2+t54-t56+t59
    t34 = t5+t6
    t38 = t19+t20 # R31
    t39 = X1*t38
    t40 = t21-t22 # R32
    t41 = Y1*t40
    t42 = t13*t14*t34
    t43 = t42+1.0 # R33
    t44 = Z1*t43
    t23 = t3-t39+t41+t44
    t25 = 1.0/(t8**(3.0/2))
    t26 = 1.0/(t8**2)
    t35 = t12*t14*w1*w2
    t36 = t5*t10*t25*w3
    t37 = t5*t13*t26*w3*2.0
    t46 = t10*t25*w1*w3
    t47 = t5*t10*t25*w2
    t48 = t5*t13*t26*w2*2.0
    t49 = t10*t11
    t50 = t5*t12*t14
    t51 = t13*t26*w1*w2*w3*2.0
    t52 = t10*t25*w1*w2*w3
    t60 = t15*t15
    t61 = t18*t18
    t62 = t23*t23
    t63 = t60+t61+t62  # lambda_i **2
    t64 = t5*t10*t25
    t65 = 1.0/sqrt(t63)  # 1/lambda_i
    t66 = Y1*r2*t6
    t67 = Z1*r3*t7
    t68 = r1*t1*t5
    t69 = r1*t1*t6
    t70 = r1*t1*t7
    t71 = r2*t2*t5
    t72 = r2*t2*t6
    t73 = r2*t2*t7
    t74 = r3*t3*t5
    t75 = r3*t3*t6
    t76 = r3*t3*t7
    t77 = X1*r1*t5
    t78 = X1*r2*w1*w2
    t79 = X1*r3*w1*w3
    t80 = Y1*r1*w1*w2
    t81 = Y1*r3*w2*w3
    t82 = Z1*r1*w1*w3
    t83 = Z1*r2*w2*w3
    t84 = X1*r1*t6*t12
    t85 = X1*r1*t7*t12
    t86 = Y1*r2*t5*t12
    t87 = Y1*r2*t7*t12
    t88 = Z1*r3*t5*t12
    t89 = Z1*r3*t6*t12
    t90 = X1*r2*t9*t10*w3
    t91 = Y1*r3*t9*t10*w1
    t92 = Z1*r1*t9*t10*w2
    t102 = X1*r3*t9*t10*w2
    t103 = Y1*r1*t9*t10*w3
    t104 = Z1*r2*t9*t10*w1
    t105 = X1*r2*t12*w1*w2
    t106 = X1*r3*t12*w1*w3
    t107 = Y1*r1*t12*w1*w2
    t108 = Y1*r3*t12*w2*w3
    t109 = Z1*r1*t12*w1*w3
    t110 = Z1*r2*t12*w2*w3
    t93 = t66+t67+t68+t69+t70+t71+t72+t73+t74+t75+t76+t77+t78+t79+t80+t81+t82+t83+t84+t85+t86+t87+t88+t89+t90+t91+t92-t102-t103-t104-t105-t106-t107-t108-t109-t110
    t94 = t10*t25*w1*w2
    t95 = t6*t10*t25*w3
    t96 = t6*t13*t26*w3*2.0
    t97 = t12*t14*w2*w3
    t98 = t6*t10*t25*w1
    t99 = t6*t13*t26*w1*2.0
    t100 = t6*t10*t25
    t101 = 1.0/sqrt(t63**3)
    t111 = t6*t12*t14
    t112 = t10*t25*w2*w3
    t113 = t12*t14*w1*w3
    t114 = t7*t10*t25*w2
    t115 = t7*t13*t26*w2*2.0
    t116 = t7*t10*t25*w1
    t117 = t7*t13*t26*w1*2.0
    t118 = t7*t12*t14
    t119 = t13*t24*t26*w1*2.0
    t120 = t10*t24*t25*w1
    t121 = t119+t120
    t122 = t13*t26*t34*w1*2.0
    t123 = t10*t25*t34*w1
    t131 = t13*t14*w1*2.0
    t124 = t122+t123-t131
    t139 = t13*t14*w3
    t125 = -t35+t36+t37+t94-t139
    t126 = X1*t125
    t127 = t49+t50+t51+t52-t64
    t128 = Y1*t127
    t129 = t126+t128-Z1*t124
    t130 = t23*t129*2.0
    t132 = t13*t26*t45*w1*2.0
    t133 = t10*t25*t45*w1
    t138 = t13*t14*w2
    t134 = -t46+t47+t48+t113-t138
    t135 = X1*t134
    t136 = -t49-t50+t51+t52+t64
    t137 = Z1*t136
    t140 = X1*s1*t5
    t141 = Y1*s2*t6
    t142 = Z1*s3*t7
    t143 = s1*t1*t5
    t144 = s1*t1*t6
    t145 = s1*t1*t7
    t146 = s2*t2*t5
    t147 = s2*t2*t6
    t148 = s2*t2*t7
    t149 = s3*t3*t5
    t150 = s3*t3*t6
    t151 = s3*t3*t7
    t152 = X1*s2*w1*w2
    t153 = X1*s3*w1*w3
    t154 = Y1*s1*w1*w2
    t155 = Y1*s3*w2*w3
    t156 = Z1*s1*w1*w3
    t157 = Z1*s2*w2*w3
    t158 = X1*s1*t6*t12
    t159 = X1*s1*t7*t12
    t160 = Y1*s2*t5*t12
    t161 = Y1*s2*t7*t12
    t162 = Z1*s3*t5*t12
    t163 = Z1*s3*t6*t12
    t164 = X1*s2*t9*t10*w3
    t165 = Y1*s3*t9*t10*w1
    t166 = Z1*s1*t9*t10*w2
    t183 = X1*s3*t9*t10*w2
    t184 = Y1*s1*t9*t10*w3
    t185 = Z1*s2*t9*t10*w1
    t186 = X1*s2*t12*w1*w2
    t187 = X1*s3*t12*w1*w3
    t188 = Y1*s1*t12*w1*w2
    t189 = Y1*s3*t12*w2*w3
    t190 = Z1*s1*t12*w1*w3
    t191 = Z1*s2*t12*w2*w3
    t167 = t140+t141+t142+t143+t144+t145+t146+t147+t148+t149+t150+t151+t152+t153+t154+t155+t156+t157+t158+t159+t160+t161+t162+t163+t164+t165+t166-t183-t184-t185-t186-t187-t188-t189-t190-t191
    t168 = t13*t26*t45*w2*2.0
    t169 = t10*t25*t45*w2
    t170 = t168+t169
    t171 = t13*t26*t34*w2*2.0
    t172 = t10*t25*t34*w2
    t176 = t13*t14*w2*2.0
    t173 = t171+t172-t176
    t174 = -t49+t51+t52+t100-t111
    t175 = X1*t174
    t177 = t13*t24*t26*w2*2.0
    t178 = t10*t24*t25*w2
    t192 = t13*t14*w1
    t179 = -t97+t98+t99+t112-t192
    t180 = Y1*t179
    t181 = t49+t51+t52-t100+t111
    t182 = Z1*t181
    t193 = t13*t26*t34*w3*2.0
    t194 = t10*t25*t34*w3
    t195 = t193+t194
    t196 = t13*t26*t45*w3*2.0
    t197 = t10*t25*t45*w3
    t200 = t13*t14*w3*2.0
    t198 = t196+t197-t200
    t199 = t7*t10*t25
    t201 = t13*t24*t26*w3*2.0
    t202 = t10*t24*t25*w3
    t203 = -t49+t51+t52-t118+t199
    t204 = Y1*t203
    t205 = t1*2.0
    t206 = Z1*t29*2.0
    t207 = X1*t32*2.0
    t208 = t205+t206+t207-Y1*t27*2.0
    t209 = t2*2.0
    t210 = X1*t53*2.0
    t211 = Y1*t58*2.0
    t212 = t209+t210+t211-Z1*t55*2.0
    t213 = t3*2.0
    t214 = Y1*t40*2.0
    t215 = Z1*t43*2.0
    t216 = t213+t214+t215-X1*t38*2.0

    jac[0, 0] = t14*t65*(X1*r1*w1*2.0+X1*r2*w2+X1*r3*w3+Y1*r1*w2+Z1*r1*w3+r1*t1*w1*2.0+r2*t2*w1*2.0+r3*t3*w1*2.0+Y1*r3*t5*t12+Y1*r3*t9*t10-Z1*r2*t5*t12-Z1*r2*t9*t10-X1*r2*t12*w2-X1*r3*t12*w3-Y1*r1*t12*w2+Y1*r2*t12*w1*2.0-Z1*r1*t12*w3+Z1*r3*t12*w1*2.0+Y1*r3*t5*t10*t11-Z1*r2*t5*t10*t11+X1*r2*t12*w1*w3-X1*r3*t12*w1*w2-Y1*r1*t12*w1*w3+Z1*r1*t12*w1*w2-Y1*r1*t10*t11*w1*w3+Z1*r1*t10*t11*w1*w2-X1*r1*t6*t10*t11*w1-X1*r1*t7*t10*t11*w1+X1*r2*t5*t10*t11*w2+X1*r3*t5*t10*t11*w3+Y1*r1*t5*t10*t11*w2-Y1*r2*t5*t10*t11*w1-Y1*r2*t7*t10*t11*w1+Z1*r1*t5*t10*t11*w3-Z1*r3*t5*t10*t11*w1-Z1*r3*t6*t10*t11*w1+X1*r2*t10*t11*w1*w3-X1*r3*t10*t11*w1*w2+Y1*r3*t10*t11*w1*w2*w3+Z1*r2*t10*t11*w1*w2*w3)-t26*t65*t93*w1*2.0-t14*t93*t101*(t130+t15*(-X1*t121+Y1*(t46+t47+t48-t13*t14*w2-t12*t14*w1*w3)+Z1*(t35+t36+t37-t13*t14*w3-t10*t25*w1*w2))*2.0+t18*(t135+t137-Y1*(t132+t133-t13*t14*w1*2.0))*2.0)*(1.0/2.0)
    jac[0, 1] = t14*t65*(X1*r2*w1+Y1*r1*w1+Y1*r2*w2*2.0+Y1*r3*w3+Z1*r2*w3+r1*t1*w2*2.0+r2*t2*w2*2.0+r3*t3*w2*2.0-X1*r3*t6*t12-X1*r3*t9*t10+Z1*r1*t6*t12+Z1*r1*t9*t10+X1*r1*t12*w2*2.0-X1*r2*t12*w1-Y1*r1*t12*w1-Y1*r3*t12*w3-Z1*r2*t12*w3+Z1*r3*t12*w2*2.0-X1*r3*t6*t10*t11+Z1*r1*t6*t10*t11+X1*r2*t12*w2*w3-Y1*r1*t12*w2*w3+Y1*r3*t12*w1*w2-Z1*r2*t12*w1*w2-Y1*r1*t10*t11*w2*w3+Y1*r3*t10*t11*w1*w2-Z1*r2*t10*t11*w1*w2-X1*r1*t6*t10*t11*w2+X1*r2*t6*t10*t11*w1-X1*r1*t7*t10*t11*w2+Y1*r1*t6*t10*t11*w1-Y1*r2*t5*t10*t11*w2-Y1*r2*t7*t10*t11*w2+Y1*r3*t6*t10*t11*w3-Z1*r3*t5*t10*t11*w2+Z1*r2*t6*t10*t11*w3-Z1*r3*t6*t10*t11*w2+X1*r2*t10*t11*w2*w3+X1*r3*t10*t11*w1*w2*w3+Z1*r1*t10*t11*w1*w2*w3)-t26*t65*t93*w2*2.0-t14*t93*t101*(t18*(Z1*(-t35+t94+t95+t96-t13*t14*w3)-Y1*t170+X1*(t97+t98+t99-t13*t14*w1-t10*t25*w2*w3))*2.0+t15*(t180+t182-X1*(t177+t178-t13*t14*w2*2.0))*2.0+t23*(t175+Y1*(t35-t94+t95+t96-t13*t14*w3)-Z1*t173)*2.0)*(1.0/2.0)
    jac[0, 2] = t14*t65*(X1*r3*w1+Y1*r3*w2+Z1*r1*w1+Z1*r2*w2+Z1*r3*w3*2.0+r1*t1*w3*2.0+r2*t2*w3*2.0+r3*t3*w3*2.0+X1*r2*t7*t12+X1*r2*t9*t10-Y1*r1*t7*t12-Y1*r1*t9*t10+X1*r1*t12*w3*2.0-X1*r3*t12*w1+Y1*r2*t12*w3*2.0-Y1*r3*t12*w2-Z1*r1*t12*w1-Z1*r2*t12*w2+X1*r2*t7*t10*t11-Y1*r1*t7*t10*t11-X1*r3*t12*w2*w3+Y1*r3*t12*w1*w3+Z1*r1*t12*w2*w3-Z1*r2*t12*w1*w3+Y1*r3*t10*t11*w1*w3+Z1*r1*t10*t11*w2*w3-Z1*r2*t10*t11*w1*w3-X1*r1*t6*t10*t11*w3-X1*r1*t7*t10*t11*w3+X1*r3*t7*t10*t11*w1-Y1*r2*t5*t10*t11*w3-Y1*r2*t7*t10*t11*w3+Y1*r3*t7*t10*t11*w2+Z1*r1*t7*t10*t11*w1+Z1*r2*t7*t10*t11*w2-Z1*r3*t5*t10*t11*w3-Z1*r3*t6*t10*t11*w3-X1*r3*t10*t11*w2*w3+X1*r2*t10*t11*w1*w2*w3+Y1*r1*t10*t11*w1*w2*w3)-t26*t65*t93*w3*2.0-t14*t93*t101*(t18*(Z1*(t46-t113+t114+t115-t13*t14*w2)-Y1*t198+X1*(t49+t51+t52+t118-t7*t10*t25))*2.0+t23*(X1*(-t97+t112+t116+t117-t13*t14*w1)+Y1*(-t46+t113+t114+t115-t13*t14*w2)-Z1*t195)*2.0+t15*(t204+Z1*(t97-t112+t116+t117-t13*t14*w1)-X1*(t201+t202-t13*t14*w3*2.0))*2.0)*(1.0/2.0)
    jac[0, 3] = r1*t65-t14*t93*t101*t208*(1.0/2.0)
    jac[0, 4] = r2*t65-t14*t93*t101*t212*(1.0/2.0)
    jac[0, 5] = r3*t65-t14*t93*t101*t216*(1.0/2.0)
    jac[1, 0] = t14*t65*(X1*s1*w1*2.0+X1*s2*w2+X1*s3*w3+Y1*s1*w2+Z1*s1*w3+s1*t1*w1*2.0+s2*t2*w1*2.0+s3*t3*w1*2.0+Y1*s3*t5*t12+Y1*s3*t9*t10-Z1*s2*t5*t12-Z1*s2*t9*t10-X1*s2*t12*w2-X1*s3*t12*w3-Y1*s1*t12*w2+Y1*s2*t12*w1*2.0-Z1*s1*t12*w3+Z1*s3*t12*w1*2.0+Y1*s3*t5*t10*t11-Z1*s2*t5*t10*t11+X1*s2*t12*w1*w3-X1*s3*t12*w1*w2-Y1*s1*t12*w1*w3+Z1*s1*t12*w1*w2+X1*s2*t10*t11*w1*w3-X1*s3*t10*t11*w1*w2-Y1*s1*t10*t11*w1*w3+Z1*s1*t10*t11*w1*w2-X1*s1*t6*t10*t11*w1-X1*s1*t7*t10*t11*w1+X1*s2*t5*t10*t11*w2+X1*s3*t5*t10*t11*w3+Y1*s1*t5*t10*t11*w2-Y1*s2*t5*t10*t11*w1-Y1*s2*t7*t10*t11*w1+Z1*s1*t5*t10*t11*w3-Z1*s3*t5*t10*t11*w1-Z1*s3*t6*t10*t11*w1+Y1*s3*t10*t11*w1*w2*w3+Z1*s2*t10*t11*w1*w2*w3)-t14*t101*t167*(t130+t15*(Y1*(t46+t47+t48-t113-t138)+Z1*(t35+t36+t37-t94-t139)-X1*t121)*2.0+t18*(t135+t137-Y1*(-t131+t132+t133))*2.0)*(1.0/2.0)-t26*t65*t167*w1*2.0
    jac[1, 1] = t14*t65*(X1*s2*w1+Y1*s1*w1+Y1*s2*w2*2.0+Y1*s3*w3+Z1*s2*w3+s1*t1*w2*2.0+s2*t2*w2*2.0+s3*t3*w2*2.0-X1*s3*t6*t12-X1*s3*t9*t10+Z1*s1*t6*t12+Z1*s1*t9*t10+X1*s1*t12*w2*2.0-X1*s2*t12*w1-Y1*s1*t12*w1-Y1*s3*t12*w3-Z1*s2*t12*w3+Z1*s3*t12*w2*2.0-X1*s3*t6*t10*t11+Z1*s1*t6*t10*t11+X1*s2*t12*w2*w3-Y1*s1*t12*w2*w3+Y1*s3*t12*w1*w2-Z1*s2*t12*w1*w2+X1*s2*t10*t11*w2*w3-Y1*s1*t10*t11*w2*w3+Y1*s3*t10*t11*w1*w2-Z1*s2*t10*t11*w1*w2-X1*s1*t6*t10*t11*w2+X1*s2*t6*t10*t11*w1-X1*s1*t7*t10*t11*w2+Y1*s1*t6*t10*t11*w1-Y1*s2*t5*t10*t11*w2-Y1*s2*t7*t10*t11*w2+Y1*s3*t6*t10*t11*w3-Z1*s3*t5*t10*t11*w2+Z1*s2*t6*t10*t11*w3-Z1*s3*t6*t10*t11*w2+X1*s3*t10*t11*w1*w2*w3+Z1*s1*t10*t11*w1*w2*w3)-t26*t65*t167*w2*2.0-t14*t101*t167*(t18*(X1*(t97+t98+t99-t112-t192)+Z1*(-t35+t94+t95+t96-t139)-Y1*t170)*2.0+t15*(t180+t182-X1*(-t176+t177+t178))*2.0+t23*(t175+Y1*(t35-t94+t95+t96-t139)-Z1*t173)*2.0)*(1.0/2.0)
    jac[1, 2] = t14*t65*(X1*s3*w1+Y1*s3*w2+Z1*s1*w1+Z1*s2*w2+Z1*s3*w3*2.0+s1*t1*w3*2.0+s2*t2*w3*2.0+s3*t3*w3*2.0+X1*s2*t7*t12+X1*s2*t9*t10-Y1*s1*t7*t12-Y1*s1*t9*t10+X1*s1*t12*w3*2.0-X1*s3*t12*w1+Y1*s2*t12*w3*2.0-Y1*s3*t12*w2-Z1*s1*t12*w1-Z1*s2*t12*w2+X1*s2*t7*t10*t11-Y1*s1*t7*t10*t11-X1*s3*t12*w2*w3+Y1*s3*t12*w1*w3+Z1*s1*t12*w2*w3-Z1*s2*t12*w1*w3-X1*s3*t10*t11*w2*w3+Y1*s3*t10*t11*w1*w3+Z1*s1*t10*t11*w2*w3-Z1*s2*t10*t11*w1*w3-X1*s1*t6*t10*t11*w3-X1*s1*t7*t10*t11*w3+X1*s3*t7*t10*t11*w1-Y1*s2*t5*t10*t11*w3-Y1*s2*t7*t10*t11*w3+Y1*s3*t7*t10*t11*w2+Z1*s1*t7*t10*t11*w1+Z1*s2*t7*t10*t11*w2-Z1*s3*t5*t10*t11*w3-Z1*s3*t6*t10*t11*w3+X1*s2*t10*t11*w1*w2*w3+Y1*s1*t10*t11*w1*w2*w3)-t26*t65*t167*w3*2.0-t14*t101*t167*(t18*(Z1*(t46-t113+t114+t115-t138)-Y1*t198+X1*(t49+t51+t52+t118-t199))*2.0+t23*(X1*(-t97+t112+t116+t117-t192)+Y1*(-t46+t113+t114+t115-t138)-Z1*t195)*2.0+t15*(t204+Z1*(t97-t112+t116+t117-t192)-X1*(-t200+t201+t202))*2.0)*(1.0/2.0)
    jac[1, 3] = s1*t65-t14*t101*t167*t208*(1.0/2.0)
    jac[1, 4] = s2*t65-t14*t101*t167*t212*(1.0/2.0)
    jac[1, 5] = s3*t65-t14*t101*t167*t216*(1.0/2.0)

    return np.matrix(jac)


# Residuals and jacobians for all points
# Compute the jacobians
def jacobians(w_pts, nullspace_r, nullspace_s, x):
    nb_obs = w_pts.shape[1]
    nb_unknowns = 6
    w = np.matrix(x[0:3])
    T = np.matrix(x[3:6])
    jacobians = np.matrix(np.zeros((2*nb_obs,nb_unknowns)))
    for i in range(nb_obs):
        # jacs
        jac = jacobian(w_pts[:,i],nullspace_r[:,i], nullspace_s[:,i], w, T)
        jacobians[2*i  ,:] = jac[0,:]
        jacobians[2*i+1,:] = jac[1,:]
    return jacobians

# Compute the residuals and jacobians for a set of points, a transformation x and the corresponding nullspaces
def residuals_and_jacobians(w_pts, nullspace_r, nullspace_s, x):
    nb_obs = w_pts.shape[1]
    nb_unknowns = 6
    w = x[0:3]
    R = rod2rot(w)
    T = np.matrix(x[3:6])

    residuals = np.matrix(np.zeros((2*nb_obs,1)))
    jacobians = np.matrix(np.zeros((2*nb_obs,nb_unknowns)))

    for i in range(nb_obs):
        # pi = R*pi + T
        p_i = R @ w_pts[:,i] + T
        p_i /= np.linalg.norm(p_i)
        # [dr, ds]^T = J_v_r(pi) * pi
        # r = nullspace[i]^T * pi
        residuals[2*i  ,0] = nullspace_r[:,i] @ p_i
        residuals[2*i+1,0] = nullspace_s[:,i] @ p_i
        # jacs
        jac = jacobian(w_pts[:,i],nullspace_r[:,i], nullspace_s[:,i], w, T)
        jacobians[2*i  ,:] = jac[0,:]
        jacobians[2*i+1,:] = jac[1,:]
    return jacobians, residuals

# Gauss Newton optimization for MLPnP solution
# Refine the 6D transformation x, from a set a points, the corresponding nullspaces, the covariance matrix P, and the initial guess for x
def refine_gauss_newton(x, w_pts, nullspace_r, nullspace_s, P, use_cov):
    nb_obs = w_pts.shape[1]
    nb_unknowns = 6
    assert ((2 * nb_obs - 6) > 0)

    # Set matrices
    r = np.matrix(np.zeros(2*nb_obs))
    rd = np.matrix(np.zeros(2*nb_obs))
    dx = np.matrix(np.zeros((nb_unknowns, 1)))
    eyeMat = np.matrix(np.identity(nb_unknowns))

    iter = 0
    stop = False
    max_it = 5
    eps = 1e-6

    while iter < max_it and not stop:
        jacs, r = residuals_and_jacobians(w_pts, nullspace_r, nullspace_s, x)
        if use_cov: JacTP = jacs.transpose() @ P
        else      : JacTP = jacs.transpose()
        # Design matrix
        N = JacTP @ jacs
        # Get system
        g = JacTP @ r

        # Solve
        # chol = npl.cholesky(N)
        # dx = npl.solve(chol,g)
        dx = npl.pinv(N) @ g
        if np.amax(np.absolute(np.asarray(dx))) > 5. or np.amin(np.absolute(np.asarray(dx))) > 1.: break
        dl = jacs @ dx

        # Update transformation vector
        if np.amax(np.absolute(np.asarray(dl))) < eps:
            stop = True
            x = x - dx
            break
        else:
            x = x - dx
        iter += 1

    return x


### MLPNP
""" Estimate 4x4 transform matrix (world to camera) from a set of N 3D points
    (in the world coordinate system), the corresponding bearing vectors
    (image rays), and the measurements covariance matrix (size 9*N) if available
"""
def mlpnp(w_pts, v, cov = None, use_gn = False):
    assert w_pts.shape[1] > 5
    use_cov = (cov is not None)
    # Definitions
    nb_pts = w_pts.shape[1]
    nullspace_r = np.zeros((3,nb_pts))
    nullspace_s = np.zeros((3,nb_pts))
    cov_reduced = np.zeros((2,2,nb_pts))

    ### TODO : planar case

    # Compute nullspaces for each observed data
    for i in range(nb_pts):
        null_2d = null_space(v[:,i].transpose())
        nullspace_r[:,i] = null_2d[:,0]
        nullspace_s[:,i] = null_2d[:,1]
        if use_cov:
            cov_reduced[:,:,i] = npl.inv(null_2d.transpose() @ np.reshape(cov[:,i],(3,3)) @ null_2d)

    # Empty stochastic model
    P = np.matrix(np.identity(2*nb_pts))
    # Empty design matrix
    A = np.matrix(np.zeros((2*nb_pts,12)))
    # Iteratively go through observations to build stochastic model and design matrix
    for i in range(nb_pts):
        # Covariance
        if use_cov: P[2*i:2*(i+1),2*i:2*(i+1)] = cov_reduced[:,:,i]
        # r11
        A[2*i  , 0] = nullspace_r[0,i] * w_pts[0,i]
        A[2*i+1, 0] = nullspace_s[0,i] * w_pts[0,i]
        # r12
        A[2*i  , 1] = nullspace_r[0,i] * w_pts[1,i]
        A[2*i+1, 1] = nullspace_s[0,i] * w_pts[1,i]
        # r13
        A[2*i  , 2] = nullspace_r[0,i] * w_pts[2,i]
        A[2*i+1, 2] = nullspace_s[0,i] * w_pts[2,i]
        # r21
        A[2*i  , 3] = nullspace_r[1,i] * w_pts[0,i]
        A[2*i+1, 3] = nullspace_s[1,i] * w_pts[0,i]
        # r22
        A[2*i  , 4] = nullspace_r[1,i] * w_pts[1,i]
        A[2*i+1, 4] = nullspace_s[1,i] * w_pts[1,i]
        # r23
        A[2*i  , 5] = nullspace_r[1,i] * w_pts[2,i]
        A[2*i+1, 5] = nullspace_s[1,i] * w_pts[2,i]
        # r31
        A[2*i  , 6] = nullspace_r[2,i] * w_pts[0,i]
        A[2*i+1, 6] = nullspace_s[2,i] * w_pts[0,i]
        # r32
        A[2*i  , 7] = nullspace_r[2,i] * w_pts[1,i]
        A[2*i+1, 7] = nullspace_s[2,i] * w_pts[1,i]
        # r33
        A[2*i  , 8] = nullspace_r[2,i] * w_pts[2,i]
        A[2*i+1, 8] = nullspace_s[2,i] * w_pts[2,i]
        # t1
        A[2*i  , 9] = nullspace_r[0,i]
        A[2*i+1, 9] = nullspace_s[0,i]
        # t2
        A[2*i  ,10] = nullspace_r[1,i]
        A[2*i+1,10] = nullspace_s[1,i]
        # t3
        A[2*i  ,11] = nullspace_r[2,i]
        A[2*i+1,11] = nullspace_s[2,i]

    # N = AtPAx
    N = A.transpose() @ P @ A
    # SVD of N
    _,_,V = npl.svd(A)
    V = V.transpose()
    R_tmp = np.reshape(V[0:9,-1],(3,3))
    # SVD to find the best rotation matrix in the Frobenius sense
    Ur,_,VHr = npl.svd(R_tmp.transpose())
    R = np.matrix(Ur.dot(VHr))
    if npl.det(R) < 0: R = -1*R
    R_inv = npl.inv(R)
    # Recover translation
    t = np.matrix(V[9:12,-1])
    t /= ( npl.norm(R_tmp[:,0],axis = 0)*npl.norm(R_tmp[:,1])*npl.norm(R_tmp[:,2]) )**(1./3)
    t = R @ t

    # Find the best solution with 6 correspondences
    diff1 = 0
    diff2 = 0
    for i in range(6):
        testres1 = R_inv @ (w_pts[:,i] - t)
        testres2 = R_inv @ (w_pts[:,i] + t)
        testres1 = testres1 / npl.norm(testres1)
        testres2 = testres2 / npl.norm(testres2)
        diff1 += 1-np.dot(testres1.transpose(), v[:,i])
        diff2 += 1-np.dot(testres2.transpose(), v[:,i])
    if diff1 <= diff2:  trans = -R_inv @ t
    else:               trans =  R_inv @ t

    x = np.matrix(np.concatenate((rot2rod(R_inv),trans)))

    # Refine with Gauss Newton
    if use_gn:
        x_gn = refine_gauss_newton(x, w_pts, nullspace_r, nullspace_s, P, use_cov)
    else:
        x_gn = [0]

    # Covariance matrix of unknown transformation parameters
    # Sigma_r,t is paper (eq. 23)
    jacs = jacobians(w_pts, nullspace_r, nullspace_s, x)
    sigma = npl.inv(jacs.transpose() @ P @ jacs)

    return np.around(x,10), np.around(x_gn,10), sigma


### PROJECTION
# Project observed pixel from image plane to camera frame, and
# propagate the observation covariance through the projection and transform it to desired shape
# We assume the perspective case (pinhole model), hence pi is K^(-1)
# eq. (2) to (6) in paper
# K     : (3x3) cinvamera intrinsics matrix -- pi in paper
# pix   : (2,n) or (3,n) matrix, each collumn corresponds to an observed pixel -- x' in paper
# cov   : (4,n) matrix, each collum corresponds to the (2,2) covariance matrix for each observations -- Sigma_x'x' in paper
# output: (3,n) matrix, each collum corresponds to the projected ray for each pixel -- v in paper
#         (9,n) matrix, each collum corresponds to the propagate covariance through the observation -- Sigma_vv in paper
def pix2rays(K, pix, cov = None):
    # Add z coordinate if not already existing (=1, on image plane)
    if pix.shape[0] == 2:
        pix = np.concatenate((pix,np.ones((pix.shape[1],1)).transpose()), axis = 0)
    x = npl.inv(K[0:3,0:3])*pix
    norm_x = npl.norm(x,axis = 0)
    v = np.matrix(x / norm_x)

    # If observation covariance is provided, propagate it
    if cov is None:
        sigma_v = None
    else:
        nb_pts = pix.shape[1]
        sigma_v = np.matrix(np.zeros((9,nb_pts)))
        sigma_x = np.matrix(np.zeros((3,3)))
        for i in range(nb_pts):
            # Propagate covariance through projection
            # Sigma_xx in paper (eq. 3 and 4
            # Instead of using eq. (4) from the paper, we rather use eq. (1) from [Forstner 2010]
            # which doesn't use the jacobian of the projection. The results seems more realistic.
            sigma_x[0:2,0:2] = cov[:,i].reshape((2,2))
            # Compute normalization jacobian
            # J in paper (eq. 6)
            J = 1/norm_x[i] - (np.eye(3) - v[:,i] @ v[:,i].transpose())
            # Propagate covariance through spherical normalization
            # Sigma_vv in paper (eq. 6)
            sigma_v[:,i] = (J @ sigma_x @ J.transpose()).reshape((9,1))

    return v, sigma_v


### MAIN
""" The main functions generate a random [R,T] transformation, then generates
    random points in the image frame.
    Then these points are converted in the camera coordinates system then
    the world coordinates system.
    Doing this in this order ensures that generated world points are contained
    inside the camera field of view.
    At this point we have :
        * A transformation from world to camera frames
        * A set of world points of known coordinates
        * A set of corresponding image measurements (rays)
    Then, we noise the image measurements and use the PnP to try to recover the
    transformation)
"""
if __name__ == '__main__':
    # Intrinsics matrix
    K = np.matrix('640 1 320 ; 0 480 240 ; 0 0 1')

    nb_iter = 1
    display = True
    randomize = True
    use_gn = False

    count_ok = 0
    count_ko = 0
    ls_time = []
    ls_prec = []
    ls_p_gn = []
    for i in range(nb_iter):
        # Ground truth transformation from world to cam
        if randomize:
            phi = random.uniform(-pi+0.001, pi-0.001)
            axis = np.matrix(np.random.random((3,1)))
            trans = np.matrix(np.random.random((3,1)) * random.uniform(1,10))
        else:
            phi = 1530
            phi = (phi + pi)%2*pi - pi
            phi = 0
            axis = np.matrix('-1.818 -0.237 -2.086').transpose()
            trans = np.matrix('0 1 1').transpose()
        axis = axis/npl.norm(axis)
        rod = phi*axis
        x_gt = np.concatenate((rod,trans), axis = 0)

        # Sample random points in image space
        nb_pts = 8 # Number of points to generate
        pix = np.concatenate((np.random.randint(0,640,(1,nb_pts)), np.random.randint(0,480,(1,nb_pts))), axis = 0)
        # Generate random covariance
        cov = None
        # cov = np.random.rand(4,nb_pts)
        # Convert those pixels to rays
        # v_i and sigma_vv from paper
        obs_rays, cov = pix2rays(K,pix,cov)

        # Sample random distances for world coordinates
        # lambda_i from paper
        min_dist = 2
        max_dist = 3
        depths = np.random.uniform(min_dist,max_dist,(nb_pts))

        # Compute 3D points positions in camera coordinates
        # lambda_i * v_i from paper
        cam_pts = obs_rays * np.diag(depths)

        # Convert to world coordinates
        # p_i from paper
        world_pts = npl.inv(rod2rot(x_gt[0:3])) @ (cam_pts - np.repeat(x_gt[3:6],nb_pts, axis = 1))

        # Noise "observed" rays with gaussian noise
        noise_sd = 0.0001
        noise = np.random.normal(0,noise_sd,obs_rays.shape)
        obs_rays += noise

        # OpenCV comparisons
        # print(world_pts.shape)
        # print(obs_rays.shape)
        w_pts=[]
        i_pts=[]
        for i in range (nb_pts):
            w_pts.append(world_pts[:,i])
            i_pts.append(pix[:,i])

        obj_2d_points = np.array(i_pts, dtype=float)
        obj_3d_points = np.array(w_pts, dtype=float)
        obj_2d_points = obj_2d_points.reshape((nb_pts,2,1))

        # print(obj_2d_points.shape)
        # print(obj_3d_points.shape)

        # Apply PnP
        tic = time.time()
        x, x_gn, sigma_rt = mlpnp(world_pts, obs_rays, cov, use_gn)
        _,r,t = cv2.solvePnP(obj_3d_points, obj_2d_points, K, cv2.SOLVEPNP_DLS)
        x_cv2 = np.matrix(np.concatenate((r,t)))
        tac = time.time()
        err_pnp = npl.norm(x_gt-x)
        err_gn = npl.norm(x_gt-x_gn)
        if display:
            print('x_gt  :\n', x_gt)
            print('x_cv2 :\n', x_cv2)
            print('x_pnp :\n', x)
            print('error :', err_pnp)
            if use_gn:
                print('x_gn :\n', x_gn)
                print('error :', err_gn, '\n')
            print('covariance :\n', sigma_rt)
            print()
        if use_gn:
            if err_pnp < err_gn:
                count_ko += 1
            else:
                count_ok += 1
        else:
            if err_pnp > 0.05:
                count_ko += 1
            else:
                count_ok += 1
        ls_time.append(tac-tic)
        ls_prec.append(err_pnp)
        ls_p_gn.append(err_gn)

    if nb_iter != 1:
        print('score -')
        print('  ok  :', count_ok)
        print('  ko  :', count_ko)
        print('time  -')
        print('  av. :', np.mean(ls_time))
        print('  sd. :', np.std (ls_time))
        print('precision -')
        print('  av. :', np.mean(ls_prec))
        print('  sd. :', np.std (ls_prec))
        if use_gn:
            print('precision gn -')
            print('  av. :', np.mean(ls_p_gn))
            print('  sd. :', np.std (ls_p_gn))
