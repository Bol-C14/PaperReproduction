; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 16))
(declare-fun b () (_ BitVec 16))
(declare-fun a () (_ BitVec 16))
(assert
 (let ((?x116 (bvmul ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) a))) ((_ zero_extend 14) ((_ extract 1 0) ((_ extract 15 0) b))))))
(let (($x25 (and (distinct (ite (bvult b (_ bv4 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x57 (ite $x25 (bvadd ((_ extract 15 0) ((_ extract 15 0) ?x116)) ((_ extract 15 0) ((_ extract 15 0) (_ bv1 16)))) c)))
(let (($x9 (and (distinct (ite (bvult a (_ bv8 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x6 (ite $x25 (bvadd ((_ extract 15 0) (bvmul ((_ extract 15 0) a) ((_ extract 15 0) b))) ((_ extract 15 0) (_ bv1 16))) c)))
(and (distinct (ite $x9 ?x6 c) (ite $x9 ((_ extract 15 0) ?x57) c)) true)))))))
(check-sat)
